file(GLOB yml_files "*.yml")

install(FILES ${yml_files} DESTINATION ${GRC_BLOCKS_DIR})
