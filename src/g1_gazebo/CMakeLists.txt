cmake_minimum_required(VERSION 3.8)
project(g1_gazebo)

find_package(ament_cmake REQUIRED)

# Install worlds, config, and launch directories
install(DIRECTORY
  worlds
  config
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
