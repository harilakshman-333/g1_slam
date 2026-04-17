cmake_minimum_required(VERSION 3.8)
project(g1_description)

find_package(ament_cmake REQUIRED)

# Install URDF, meshes, and launch files
install(DIRECTORY
  urdf
  meshes
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
