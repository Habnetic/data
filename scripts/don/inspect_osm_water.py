import geopandas as gpd

gdf = gpd.read_file(
    "raw/DON/buildings/pais_vasco.gpkg",
    layer="gis_osm_water_a_free",
)

print("columns:")
print(list(gdf.columns))

print("\ngeometry types:")
print(gdf.geometry.geom_type.unique())

print("\nhead:")
print(gdf.head(10).drop(columns="geometry", errors="ignore"))
