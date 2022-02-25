import numpy as np
from panda3d.core import *

import open3d as o3d


def mesh_node_to_point_cloud_node(source_node):
    numOfVertex = source_node.node().getGeom(0).getVertexData().getNumRows()

    _format = GeomVertexFormat.getV3n3c4()
    vertex_data = GeomVertexData('pc', _format, Geom.UH_static)
    vertex = GeomVertexWriter(vertex_data, 'vertex')
    s_vertex = GeomVertexReader(source_node.node().getGeom(0).getVertexData(), 'vertex')
    while not s_vertex.isAtEnd():
        vertex.addData3(s_vertex.getData3())
    normal = GeomVertexWriter(vertex_data, 'normal')
    s_normal = GeomVertexReader(source_node.node().getGeom(0).getVertexData(), 'normal')
    while not s_normal.isAtEnd():
        normal.addData3(s_normal.getData3())
    color = GeomVertexWriter(vertex_data, 'color')
    s_color = GeomVertexReader(source_node.node().getGeom(0).getVertexData(), 'color')
    while not s_color.isAtEnd():
        color.addData3(s_color.getData3())

    prim = GeomPoints(Geom.UH_static)
    prim.add_next_vertices(numOfVertex)

    geom = Geom(vertex_data)
    geom.addPrimitive(prim)
    node = GeomNode('PointCloud')
    node.addGeom(geom)

    node = NodePath(node)
    return node


def geom_node_to_pcd(geom_node):
    pcd = o3d.geometry.PointCloud()

    _format = GeomVertexFormat.getV3t2()
    s_vertex = GeomVertexReader(geom_node.node().getGeom(0).getVertexData(), 'vertex')
    while not s_vertex.isAtEnd():
        vertex = s_vertex.getData3()
        pcd.points.append(vertex)

    s_normal = GeomVertexReader(geom_node.node().getGeom(0).getVertexData(), 'normal')
    while not s_normal.isAtEnd():
        normal = s_normal.getData3()
        pcd.normals.append(normal)

    s_color = GeomVertexReader(geom_node.node().getGeom(0).getVertexData(), 'color')
    while not s_color.isAtEnd():
        color = s_color.getData3()
        pcd.colors.append(color)

    return pcd


def pcd_to_geom_node(pcd):
    num_of_vertex = len(pcd.points)

    _format = GeomVertexFormat.getV3n3c4()
    vertex_data = GeomVertexData('pc', _format, Geom.UHDynamic)
    vertex_data.setNumRows(2)

    vertex = GeomVertexWriter(vertex_data, 'vertex')
    normal = GeomVertexWriter(vertex_data, 'normal')
    color = GeomVertexWriter(vertex_data, 'color')

    for point in pcd.points:
        vertex.addData3(point[0], point[1], point[2])
    for point_normal in pcd.normals:
        normal.addData3(point_normal[0], point_normal[1], point_normal[2])
    for point_color in pcd.colors:
        color.addData3(point_color[0], point_color[1], point_color[2])

    prim = GeomPoints(Geom.UH_static)
    prim.add_next_vertices(num_of_vertex)
    geom = Geom(vertex_data)
    geom.addPrimitive(prim)

    node = GeomNode('PointCloud')
    node.addGeom(geom)
    node = NodePath(node)
    return node


def color_point_cloud(source_node, feature_points, uniform_color=[1, 1, 1]):
    pcd = geom_node_to_pcd(source_node)
    pcd.paint_uniform_color(uniform_color)
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)

    for feature_point in feature_points:
        point = feature_point[0]
        radius = feature_point[1]

        [k, idx, dist] = pcd_tree.search_radius_vector_3d(point, radius)

        print('point: ', point, ', radius: ', radius)
        print(len(idx), ' / ', len(pcd.points))

        np.asarray(pcd.colors)[idx[1:], :] = [0, 1, 0]

    return pcd_to_geom_node(pcd)


def save_point_cloud(source_node, output_path):
    pcd = geom_node_to_pcd(source_node)
    o3d.io.write_point_cloud(filename=output_path, pointcloud=pcd, compressed=True)






