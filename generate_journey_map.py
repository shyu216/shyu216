#!/usr/bin/env python3
"""
Life Journey Map Generator
从journey.yml读取旅程数据，生成SVG世界地图
"""

import yaml
import math
import urllib.request
import json
import datetime
from pathlib import Path


def load_journey_data(yaml_path: str) -> dict:
    """加载旅程数据"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def download_world_data():
    """下载世界地图数据（如果不存在）"""
    world_file = Path("world-110m.json")
    if not world_file.exists():
        print("Downloading world map data...")
        try:
            url = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
            urllib.request.urlretrieve(url, world_file)
            print("World map data downloaded.")
        except Exception as e:
            print(f"Failed to download world data: {e}")
            print("Will use simplified world map instead.")


def mercator_projection(lon: float, lat: float, scale: float, center_lon: float, center_lat: float, width: float, height: float) -> tuple:
    """
    墨卡托投影 - 修正版
    将经纬度转换为SVG坐标
    """
    # 地球半径（用于投影计算）
    R = 6371

    # 转换为弧度
    lon_rad = math.radians(lon)
    lat_rad = math.radians(lat)
    center_lon_rad = math.radians(center_lon)
    center_lat_rad = math.radians(center_lat)

    # 墨卡托投影公式
    x = R * (lon_rad - center_lon_rad)
    y = -R * math.log(math.tan(math.pi/4 + lat_rad/2))

    # 中心点的投影坐标
    center_y = -R * math.log(math.tan(math.pi/4 + center_lat_rad/2))

    # 应用缩放和平移
    screen_x = width/2 + x * scale / R
    screen_y = height/2 + (y - center_y) * scale / R

    return (screen_x, screen_y)


def azimuthal_equidistant_projection(lon: float, lat: float, scale: float, center_lon: float, center_lat: float, width: float, height: float) -> tuple:
    """
    等距方位投影 (Azimuthal Equidistant Projection)

    特点:
    - 以中心点为原点，向四周等距展开
    - 保持从中心点到任意点的距离准确
    - 适合以特定地点为中心的局部地图

    算法:
    1. 在球面上计算目标点相对于中心点的方位角和距离
    2. 在切平面上按相同方位角和距离放置点

    Args:
        lon, lat: 目标点经纬度
        scale: 缩放因子 (像素/公里)
        center_lon, center_lat: 中心点经纬度
        width, height: 画布尺寸

    Returns:
        (screen_x, screen_y) 屏幕坐标
    """
    # 转换为弧度
    lon_rad = math.radians(lon)
    lat_rad = math.radians(lat)
    center_lon_rad = math.radians(center_lon)
    center_lat_rad = math.radians(center_lat)

    # 计算球面距离 c (中心角)
    delta_lon = lon_rad - center_lon_rad

    # 球面余弦公式计算中心角
    cos_c = (math.sin(center_lat_rad) * math.sin(lat_rad) +
             math.cos(center_lat_rad) * math.cos(lat_rad) * math.cos(delta_lon))

    # 限制范围避免数值误差
    cos_c = max(-1.0, min(1.0, cos_c))
    c = math.acos(cos_c)

    # 计算方位角 (bearing)
    # 使用球面三角公式
    if abs(c) < 1e-10:
        # 点在中心，方位角任意设为0
        bearing = 0
    else:
        # 计算方位角的正弦和余弦
        sin_bearing = math.cos(lat_rad) * math.sin(delta_lon) / math.sin(c)
        cos_bearing = (math.sin(lat_rad) - math.sin(center_lat_rad) * cos_c) / (math.cos(center_lat_rad) * math.sin(c))

        # 使用 atan2 获取正确象限的方位角
        bearing = math.atan2(sin_bearing, cos_bearing)

    # 地球半径 (公里)
    R = 6371

    # 计算平面距离 (公里)
    distance = R * c

    # 在切平面上放置点
    # x = distance * sin(bearing), y = -distance * cos(bearing)
    # 注意: y轴向下为正，所以需要取反
    plane_x = distance * math.sin(bearing)
    plane_y = -distance * math.cos(bearing)

    # 应用缩放并平移到画布中心
    screen_x = width/2 + plane_x * scale / R
    screen_y = height/2 + plane_y * scale / R

    return (screen_x, screen_y)


def get_projection_func(projection_type: str):
    """
    获取投影函数

    Args:
        projection_type: "mercator" 或 "azimuthal"

    Returns:
        投影函数
    """
    if projection_type.lower() == "azimuthal":
        return azimuthal_equidistant_projection
    else:
        return mercator_projection


def decode_arc(arc: list, topology: dict) -> list:
    """解码TopoJSON中的arc"""
    arcs = topology['arcs']
    
    # 处理负索引（表示反向）
    if isinstance(arc, int):
        arc_index = arc
        reverse = arc_index < 0
        if reverse:
            arc_index = ~arc_index  # 按位取反得到正索引
        
        arc_data = arcs[arc_index]
        points = []
        x, y = 0, 0
        
        for point in arc_data:
            x += point[0]
            y += point[1]
            if reverse:
                points.insert(0, [x, y])
            else:
                points.append([x, y])
        
        return points
    
    return []


def decode_arcs(arc_refs: list, topology: dict) -> list:
    """解码多个arc引用"""
    points = []
    for arc_ref in arc_refs:
        arc_points = decode_arc(arc_ref, topology)
        # 避免重复点
        if points and arc_points and points[-1] == arc_points[0]:
            points.extend(arc_points[1:])
        else:
            points.extend(arc_points)
    return points


def topology_to_geojson(topology: dict, object_name: str = 'countries') -> list:
    """将TopoJSON对象转换为坐标列表"""
    obj = topology['objects'].get(object_name)
    if not obj:
        return []
    
    features = []
    geometries = obj.get('geometries', [])
    
    for geom in geometries:
        geom_type = geom.get('type')
        arcs = geom.get('arcs', [])
        
        if geom_type == 'Polygon':
            # 单个多边形
            for ring_arcs in arcs:
                points = decode_arcs(ring_arcs, topology)
                if points:
                    features.append(points)
                    
        elif geom_type == 'MultiPolygon':
            # 多个多边形
            for polygon_arcs in arcs:
                for ring_arcs in polygon_arcs:
                    points = decode_arcs(ring_arcs, topology)
                    if points:
                        features.append(points)
    
    return features


def parse_topojson_to_svg_paths(topology: dict, projection_func) -> list:
    """将TopoJSON转换为SVG路径"""
    paths = []
    
    # 获取所有坐标
    coordinates_list = topology_to_geojson(topology, 'countries')
    
    for coords in coordinates_list:
        if not coords:
            continue
        
        # 将TopoJSON坐标（缩放后的整数）转换为经纬度
        transform = topology.get('transform', {})
        scale = transform.get('scale', [1, 1])
        translate = transform.get('translate', [0, 0])
        
        path_d = "M"
        for i, point in enumerate(coords):
            # 解码坐标
            lon = point[0] * scale[0] + translate[0]
            lat = point[1] * scale[1] + translate[1]
            
            # 投影到屏幕坐标
            x, y = projection_func(lon, lat)
            
            if i > 0:
                path_d += " L"
            path_d += f" {x:.2f},{y:.2f}"
        
        path_d += " Z"
        paths.append(path_d)
    
    return paths


def generate_graticule(projection_func, width: float, height: float, step: int = 30) -> list:
    """生成经纬网格线 - 只生成在视口内的"""
    lines = []
    
    # 经线
    for lon in range(-180, 181, step):
        points = []
        for lat in range(-70, 71, 5):
            x, y = projection_func(lon, lat)
            # 只添加在视口内的点
            if 0 <= x <= width and 0 <= y <= height:
                points.append((x, y))
        if len(points) > 1:
            d = "M" + " L".join([f"{x:.2f},{y:.2f}" for x, y in points])
            lines.append(d)
    
    # 纬线
    for lat in range(-60, 61, step):
        points = []
        for lon in range(-180, 181, 10):
            x, y = projection_func(lon, lat)
            # 只添加在视口内的点
            if 0 <= x <= width and 0 <= y <= height:
                points.append((x, y))
        if len(points) > 1:
            d = "M" + " L".join([f"{x:.2f},{y:.2f}" for x, y in points])
            lines.append(d)
    
    return lines


def generate_curved_path(start: tuple, end: tuple, curvature: float = 0.3) -> str:
    """生成曲线路径（二次贝塞尔曲线）"""
    x1, y1 = start
    x2, y2 = end
    
    # 计算控制点
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    
    # 计算垂直偏移
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist < 1:
        return f"M {x1:.2f},{y1:.2f} L {x2:.2f},{y2:.2f}"
    
    # 控制点偏移（向上弯曲）
    offset_x = -dy * curvature
    offset_y = dx * curvature
    
    ctrl_x = mid_x + offset_x
    ctrl_y = mid_y + offset_y
    
    return f"M {x1:.2f},{y1:.2f} Q {ctrl_x:.2f},{ctrl_y:.2f} {x2:.2f},{y2:.2f}"


def calculate_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两点间的大圆距离（公里）"""
    R = 6371  # 地球半径（公里）

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def hex_to_hsl(hex_color: str) -> tuple:
    """HEX 颜色转 HSL"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2

    if max_c == min_c:
        h = s = 0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        if max_c == r:
            h = ((g - b) / d + (6 if g < b else 0)) / 6
        elif max_c == g:
            h = ((b - r) / d + 2) / 6
        else:
            h = ((r - g) / d + 4) / 6

    return (h * 360, s, l)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """HSL 转 HEX 颜色"""
    h = h / 360

    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def generate_color_palette(n: int, base_colors: list = None) -> list:
    """自动生成 N 个渐变色
    
    逻辑:
    - n <= len(base_colors): 直接使用前 n 个颜色
    - n > len(base_colors): 清空，使用第一个和最后一个颜色之间渐变生成 n 个
    """
    if base_colors is None:
        base_colors = ["#8b4513", "#cd853f", "#d4a574", "#a0522d"]

    if n <= len(base_colors):
        return base_colors[:n]

    base_hsl = [hex_to_hsl(c) for c in base_colors]
    start_h = base_hsl[0][0]
    end_h = base_hsl[-1][0]
    start_s = base_hsl[0][1]
    end_s = base_hsl[-1][1]
    start_l = base_hsl[0][2]
    end_l = base_hsl[-1][2]

    colors = []
    for i in range(n):
        progress = i / max(n - 1, 1)
        
        h = start_h + (end_h - start_h) * progress
        s = start_s + (end_s - start_s) * progress
        l = start_l + (end_l - start_l) * progress

        colors.append(hsl_to_hex(h, s, l))

    return colors


def calculate_weighted_center(journey: list, isolation_factor: float = 0.8) -> tuple:
    """
    计算考虑地理分布的加权中心

    算法原理:
    - 孤立点（与其他点距离远）获得更高权重
    - 密集区域的点权重降低
    - 这样中心点会更均衡，不会被某个聚集区域"拉偏"

    Args:
        journey: 旅程数据列表
        isolation_factor: 孤立点权重因子，越大孤立点影响越大

    Returns:
        (经度, 纬度) 加权中心坐标
    """
    if not journey:
        return (0, 0)

    if len(journey) == 1:
        return journey[0]['coords']

    n = len(journey)
    coords = [loc['coords'] for loc in journey]

    # 计算每个点的平均邻近距离（密度指标）
    avg_distances = []
    for i in range(n):
        lon1, lat1 = coords[i]
        distances = []
        for j in range(n):
            if i != j:
                lon2, lat2 = coords[j]
                dist = calculate_distance(lon1, lat1, lon2, lat2)
                distances.append(dist)

        # 使用到其他点的平均距离作为密度指标
        avg_dist = sum(distances) / len(distances) if distances else 0
        avg_distances.append(avg_dist)

    # 计算最大平均距离用于归一化
    max_avg_dist = max(avg_distances) if avg_distances else 1
    min_avg_dist = min(avg_distances) if avg_distances else 0

    # 计算权重：孤立点（avg_dist大）获得高权重
    # 使用反比关系：weight = 1 / (density + epsilon)
    weights = []
    for avg_dist in avg_distances:
        if max_avg_dist == min_avg_dist:
            # 所有点密度相同，均匀权重
            weight = 1.0
        else:
            # 归一化密度 (0-1)
            normalized_density = 1 - (avg_dist - min_avg_dist) / (max_avg_dist - min_avg_dist)
            # 反比权重：密度低的点（孤立点）权重高
            # 使用 (1 - density)^factor 来调节权重分布
            weight = (1 - normalized_density + 0.1) ** isolation_factor

        weights.append(weight)

    # 归一化权重
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]

    # 计算加权中心
    weighted_lon = sum(coords[i][0] * weights[i] for i in range(n))
    weighted_lat = sum(coords[i][1] * weights[i] for i in range(n))

    return (weighted_lon, weighted_lat)


def calculate_bbox_center(journey: list) -> tuple:
    """计算边界框中心"""
    if not journey:
        return (0, 0)

    lons = [loc['coords'][0] for loc in journey]
    lats = [loc['coords'][1] for loc in journey]
    return ((min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2)


def calculate_centroid(journey: list) -> tuple:
    """计算简单重心（算术平均）"""
    if not journey:
        return (0, 0)

    total_lon = sum(loc['coords'][0] for loc in journey)
    total_lat = sum(loc['coords'][1] for loc in journey)
    n = len(journey)
    return (total_lon / n, total_lat / n)


def resolve_center(center_config, journey: list) -> tuple:
    """
    解析中心点配置

    Args:
        center_config: 中心点配置，可以是:
            - [lon, lat]: 固定坐标
            - "weighted": 加权中心（考虑地理分布）
            - "centroid": 简单重心
            - "bbox": 边界框中心
            - "melbourne": 墨尔本坐标
        journey: 旅程数据

    Returns:
        (经度, 纬度) 元组
    """
    if isinstance(center_config, list) and len(center_config) == 2:
        return (center_config[0], center_config[1])

    if isinstance(center_config, str):
        center_str = center_config.lower().strip()

        if center_str == "weighted":
            center = calculate_weighted_center(journey)
            print(f"Using weighted center: ({center[0]:.2f}, {center[1]:.2f})")
            return center

        elif center_str == "centroid":
            center = calculate_centroid(journey)
            print(f"Using centroid center: ({center[0]:.2f}, {center[1]:.2f})")
            return center

        elif center_str == "bbox":
            center = calculate_bbox_center(journey)
            print(f"Using bbox center: ({center[0]:.2f}, {center[1]:.2f})")
            return center

        elif center_str in ["melbourne", "墨尔本"]:
            return (144.9631, -37.8136)

    # 默认使用加权中心
    print("Unknown center config, using weighted center as default")
    return calculate_weighted_center(journey)


def get_simplified_world() -> dict:
    """获取简化的世界地图数据（各大洲轮廓）"""
    return {
        "type": "FeatureCollection",
        "features": [
            # 中国/东亚
            {"type": "Feature", "properties": {"name": "China"}, "geometry": {"type": "Polygon", "coordinates": [[[73, 18], [135, 18], [135, 54], [73, 54], [73, 18]]]}},
            # 澳大利亚
            {"type": "Feature", "properties": {"name": "Australia"}, "geometry": {"type": "Polygon", "coordinates": [[[113, -44], [154, -44], [154, -10], [113, -10], [113, -44]]]}},
            # 东南亚
            {"type": "Feature", "properties": {"name": "SE Asia"}, "geometry": {"type": "Polygon", "coordinates": [[[95, -11], [142, -11], [142, 20], [95, 20], [95, -11]]]}},
        ]
    }


def generate_svg(data: dict, output_path: str):
    """生成SVG地图"""
    config = data['map_config']
    journey = data['journey']

    width = config['width']
    height = config['height']
    scale = config['scale']
    projection_type = config.get('projection', 'mercator')
    center_lon, center_lat = resolve_center(config.get('center', 'weighted'), journey)
    colors = config['colors']

    # 选择投影函数
    projection_func = get_projection_func(projection_type)
    print(f"Using projection: {projection_type}")

    # 投影函数
    def project(lon, lat):
        return projection_func(lon, lat, scale, center_lon, center_lat, width, height)
    
    # 加载世界地图数据
    world_file = Path("world-110m.json")
    country_paths = []
    
    if world_file.exists():
        try:
            with open(world_file, 'r', encoding='utf-8') as f:
                world_data = json.load(f)
            
            # 检查是否是TopoJSON格式
            if world_data.get('type') == 'Topology':
                print("Loading TopoJSON world map...")
                country_paths = parse_topojson_to_svg_paths(world_data, project)
            else:
                # GeoJSON格式
                print("Loading GeoJSON world map...")
                from geojson_handler import parse_geojson_to_svg_paths
                country_paths = parse_geojson_to_svg_paths(world_data, project)
                
        except Exception as e:
            print(f"Error loading world data: {e}")
    
    # 如果没有路径，使用简化地图
    if not country_paths:
        print("Using simplified world map...")
        # 简化地图直接用矩形表示
        country_paths = [
            # 中国
            "M 483.76,324.07 L 678.54,324.07 L 678.54,179.22 L 483.76,179.22 Z",
            # 澳大利亚
            "M 609.42,535.82 L 738.23,535.82 L 738.23,413.15 L 609.42,413.15 Z",
            # 东南亚
            "M 552.88,416.35 L 700.53,416.35 L 700.53,317.43 L 552.88,317.43 Z",
        ]
    
    # 生成经纬网格
    graticule_paths = generate_graticule(project, width, height)
    
    # 投影旅程点
    journey_points = []
    for loc in journey:
        lon, lat = loc['coords']
        x, y = project(lon, lat)
        journey_points.append({
            **loc,
            'x': x,
            'y': y
        })
    
    path_count = len(journey_points) - 1
    path_colors = generate_color_palette(path_count, colors.get('path_colors', None) or ["#8b4513", "#cd853f"])
    
    journey_paths = []
    for i in range(path_count):
        start = (journey_points[i]['x'], journey_points[i]['y'])
        end = (journey_points[i+1]['x'], journey_points[i+1]['y'])
        
        dist = calculate_distance(
            journey_points[i]['coords'][0], journey_points[i]['coords'][1],
            journey_points[i+1]['coords'][0], journey_points[i+1]['coords'][1]
        )
        
        curvature = 0.25 if dist < 5000 else 0.15 if dist < 10000 else 0.08
        path_d = generate_curved_path(start, end, curvature=curvature)
        
        journey_paths.append({
            'd': path_d,
            'color': path_colors[i],
            'from': journey_points[i],
            'to': journey_points[i+1],
            'distance': dist
        })
    
    # 获取圆角设置
    border_radius = config.get('border_radius', 0)

    # 构建SVG
    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'  <defs>',
        f'    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
        f'      <feDropShadow dx="3" dy="3" stdDeviation="4" flood-color="#000000" flood-opacity="0.15"/>',
        f'    </filter>',
        f'    <clipPath id="map-clip">',
        f'      <rect width="{width}" height="{height}" rx="{border_radius}" ry="{border_radius}"/>',
        f'    </clipPath>',
        f'    <style>',
        f'      .country {{ fill: {colors["land"]}; stroke: {colors["border"]}; stroke-width: 0.5; }}',
        f'      .graticule {{ fill: none; stroke: {colors["graticule"]}; stroke-width: 0.3; stroke-opacity: 0.4; }}',
        f'      .journey-path {{ fill: none; stroke-linecap: round; stroke-dasharray: 8 4; }}',
        f'      .marker {{ filter: drop-shadow(0 0 8px currentColor); }}',
        f'      .marker-pulse {{ fill: none; stroke-width: 2; opacity: 0.6; }}',
        f'      .label {{ font-family: Georgia, serif; }}',
        f'      .compass {{ fill: none; stroke: {colors["border"]}; stroke-width: 1.5; }}',
        f'      @keyframes dash {{',
        f'        to {{ stroke-dashoffset: -24; }}',
        f'      }}',
        f'      .journey-path {{ animation: dash 1.5s linear infinite; }}',
        f'    </style>',
        f'  </defs>',
        f'',
        f'  <!-- 背景 -->',
        f'  <rect width="{width}" height="{height}" fill="{colors["background"]}" rx="{border_radius}" ry="{border_radius}"/>',
        f'',
        f'  <!-- 被裁剪的地图内容 -->',
        f'  <g clip-path="url(#map-clip)">',
        f'',
        f'  <!-- 经纬网格 -->',
    ]
    
    # 添加经纬网格
    for d in graticule_paths:
        svg_parts.append(f'  <path class="graticule" d="{d}"/>')
    
    svg_parts.append('')
    svg_parts.append('  <!-- 国家/地区 -->')
    
    # 添加国家路径
    for d in country_paths:
        svg_parts.append(f'  <path class="country" d="{d}"/>')
    
    svg_parts.append('')
    svg_parts.append('  <!-- 旅程路径 -->')
    
    # 添加旅程路径
    for i, path_info in enumerate(journey_paths):
        svg_parts.append(f'  <path class="journey-path" d="{path_info["d"]}" stroke="{path_info["color"]}" stroke-width="2.5"/>')
    
    svg_parts.append('')
    svg_parts.append('  <!-- 地点标记 -->')

    marker_colors = generate_color_palette(len(journey_points), colors.get('path_colors', None) or ["#8b4513", "#cd853f"])
    
    for i, point in enumerate(journey_points):
        color = marker_colors[i]
        is_latest = (i == len(journey_points) - 1)

        # 只给最新地点添加脉冲动画
        if is_latest:
            svg_parts.append(f'  <circle class="marker-pulse" cx="{point["x"]:.2f}" cy="{point["y"]:.2f}" r="8" stroke="{color}">')
            svg_parts.append(f'    <animate attributeName="r" values="5;8;20" dur="3s" repeatCount="indefinite"/>')
            svg_parts.append(f'    <animate attributeName="opacity" values="0.6;0.2;0" dur="3s" repeatCount="indefinite"/>')
            svg_parts.append(f'  </circle>')

        # 中心点
        svg_parts.append(f'  <circle class="marker" cx="{point["x"]:.2f}" cy="{point["y"]:.2f}" r="5" fill="{color}"/>')
    
    svg_parts.append('')
    svg_parts.append('  </g>')
    svg_parts.append('')
    svg_parts.append('  <!-- 标题 -->')
    svg_parts.append(f'  <text class="label" x="{width/2}" y="40" text-anchor="middle" fill="#5c4033" font-size="24" font-weight="bold">His Journey</text>')
    
    svg_parts.append('')
    svg_parts.append('  <!-- 罗盘装饰 -->')
    compass_x = width - 80
    compass_y = 100
    svg_parts.append(f'  <g transform="translate({compass_x}, {compass_y})" opacity="0.6">')
    svg_parts.append(f'    <circle r="38" fill="none" stroke="{colors["graticule"]}" stroke-width="0.3" stroke-dasharray="2,2"/>')
    svg_parts.append(f'    <circle r="35" class="compass"/>')
    svg_parts.append(f'    <circle r="30" fill="none" stroke="{colors["graticule"]}" stroke-width="0.5"/>')
    svg_parts.append(f'    <circle r="20" fill="none" stroke="{colors["graticule"]}" stroke-width="0.3"/>')
    svg_parts.append(f'    <line x1="0" y1="-38" x2="0" y2="38" stroke="{colors["graticule"]}" stroke-width="0.5" stroke-dasharray="3,3"/>')
    svg_parts.append(f'    <line x1="-38" y1="0" x2="38" y2="0" stroke="{colors["graticule"]}" stroke-width="0.5" stroke-dasharray="3,3"/>')
    svg_parts.append(f'    <path d="M 0 -25 L 6 -6 L 25 0 L 6 6 L 0 25 L -6 6 L -25 0 L -6 -6 Z" fill="{colors["land"]}" stroke="{colors["border"]}" stroke-width="1"/>')
    svg_parts.append(f'    <text y="-40" text-anchor="middle" fill="{colors["border"]}" font-size="11" font-weight="bold">N</text>')
    svg_parts.append(f'    <text y="50" text-anchor="middle" fill="{colors["graticule"]}" font-size="9">S</text>')
    svg_parts.append(f'    <text x="-45" y="4" text-anchor="middle" fill="{colors["graticule"]}" font-size="9">W</text>')
    svg_parts.append(f'    <text x="45" y="4" text-anchor="middle" fill="{colors["graticule"]}" font-size="9">E</text>')
    svg_parts.append(f'  </g>')

    svg_parts.append('')
    svg_parts.append('  <!-- 时间线 -->')
    timeline_y = height - 50
    timeline_margin = 60
    timeline_width = width - 2 * timeline_margin
    timeline_x = timeline_margin

    years = [point['year'] for point in journey_points]
    min_year = min(years)
    current_year = datetime.datetime.now().year
    max_year = max(current_year, max(years))
    year_range = max_year - min_year if max_year > min_year else 1

    timeline_colors = generate_color_palette(len(journey_points), colors.get('path_colors', None) or ["#8b4513", "#cd853f"])
    end_color = timeline_colors[-1]
    
    svg_parts.append(f'  <g transform="translate({timeline_x}, {timeline_y})">')
    
    for i, point in enumerate(journey_points):
        year_offset = point['year'] - min_year
        x_pos = (year_offset / year_range) * timeline_width if year_range > 0 else timeline_width / 2
        color = timeline_colors[i]
        is_latest = (i == len(journey_points) - 1)

        if i == 0:
            svg_parts.append(f'    <line x1="0" y1="-4" x2="0" y2="4" stroke="{color}" stroke-width="2"/>')
        else:
            svg_parts.append(f'    <line x1="{x_pos}" y1="-4" x2="{x_pos}" y2="4" stroke="{color}" stroke-width="2"/>')

        svg_parts.append(f'    <text x="{x_pos}" y="-12" text-anchor="middle" fill="#5c4033" font-size="13" font-weight="bold" class="label">{point["year"]}</text>')
        svg_parts.append(f'    <text x="{x_pos}" y="22" text-anchor="middle" fill="#8b7355" font-size="11" class="label">{point["city"]}</text>')
        
        if i > 0:
            prev_point = journey_points[i-1]
            dist = calculate_distance(
                prev_point['coords'][0], prev_point['coords'][1],
                point['coords'][0], point['coords'][1]
            )
            mid_x = (x_pos + ((year_offset - (point['year'] - prev_point['year'])) / year_range * timeline_width if year_range > 0 else timeline_width / 2)) / 2 if i > 1 else x_pos / 2
            dist_color = timeline_colors[i-1]
            svg_parts.append(f'    <text x="{mid_x}" y="-2" text-anchor="middle" fill="{dist_color}" font-size="8" opacity="0.7">{dist:,.0f}km</text>')

    svg_parts.append(f'    <!-- 轴线 -->')
    svg_parts.append(f'    <line x1="0" y1="0" x2="{timeline_width}" y2="0" stroke="{timeline_colors[0]}" stroke-width="1.5" stroke-dasharray="4,2"/>')
    svg_parts.append(f'    <!-- 终点光晕 -->')
    svg_parts.append(f'    <circle cx="{timeline_width}" cy="0" r="8" fill="none" stroke="{end_color}" stroke-width="2" opacity="1">')
    svg_parts.append(f'      <animate attributeName="r" values="4;6;16" dur="3s" repeatCount="indefinite"/>')
    svg_parts.append(f'      <animate attributeName="opacity" values="0.6;0.2;0" dur="3s" repeatCount="indefinite"/>')
    svg_parts.append(f'    </circle>')
    svg_parts.append(f'    <circle cx="{timeline_width}" cy="0" r="4" fill="{end_color}"/>')

    svg_parts.append(f'  </g>')
    
    update_time = datetime.datetime.now().strftime("%Y-%m-%d")
    svg_parts.append(f'  <text x="{width - 15}" y="{height - 12}" text-anchor="end" fill="{colors["graticule"]}" font-size="10" font-style="italic" opacity="0.6">Last Update: {update_time}</text>')
    
    svg_parts.append('')
    svg_parts.append('</svg>')
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_parts))
    
    print(f"SVG map generated: {output_path}")
    print(f"Total locations: {len(journey_points)}")
    print(f"Total journey distance: {sum(p['distance'] for p in journey_paths):,.0f} km")
    print(f"Country paths: {len(country_paths)}")
    print(f"Graticule lines: {len(graticule_paths)}")


def main():
    """主函数"""
    yaml_path = "journey.yml"
    output_path = "journey-map.svg"
    
    # 尝试下载世界地图数据
    download_world_data()
    
    print("Loading journey data...")
    data = load_journey_data(yaml_path)
    
    print("Generating SVG map...")
    generate_svg(data, output_path)
    
    print("Done!")


if __name__ == "__main__":
    main()
