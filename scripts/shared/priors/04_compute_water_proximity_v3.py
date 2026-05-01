from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np


CITIES = ["RTM", "HAM", "DON"]


def load_city_data(city):
    base = Path("processed") / city

    buildings = gpd.read_file(base / "derived" / f"buildings_{city.lower()}.gpkg")
    hydro = gpd.read_file(base / "derived" / f"hydrography_{city.lower()}.gpkg")
    coast = gpd.read_file(base / "derived" / "coastline_ne.gpkg")

    return buildings, hydro, coast


def to_line_reference(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    geom_types = set(gdf.geometry.geom_type.unique())

    if geom_types <= {"LineString", "MultiLineString"}:
        return gdf

    # For polygons, use boundary lines
    polygon_mask = gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    gdf.loc[polygon_mask, "geometry"] = gdf.loc[polygon_mask, "geometry"].boundary

    return gdf


def compute_nearest_distance(buildings, targets):
    from shapely.strtree import STRtree

    target_geoms = list(targets.geometry.values)
    tree = STRtree(target_geoms)

    distances = np.zeros(len(buildings))

    for i, geom in enumerate(buildings.geometry.values):
        nearest = tree.nearest(geom)

        if isinstance(nearest, (int, np.integer)):
            nearest_geom = target_geoms[int(nearest)]
        else:
            nearest_geom = nearest

        distances[i] = geom.distance(nearest_geom)

        if (i + 1) % 25_000 == 0:
            print(f"[distance] processed {i + 1:,}/{len(buildings):,}")

    return distances


def process_city(city):
    print(f"\n[city] {city}")

    bldg, hydro, coast = load_city_data(city)

    hydro = to_line_reference(hydro)
    coast = to_line_reference(coast)

    print(f"[load] buildings={len(bldg)} hydro={len(hydro)} coast={len(coast)}")

    dist_hydro = compute_nearest_distance(bldg, hydro)
    dist_coast = compute_nearest_distance(bldg, coast)

    dist_water = np.minimum(dist_hydro, dist_coast)

    out = pd.DataFrame({
        "bldg_id": bldg["bldg_id"].values,
        "dist_to_hydrography_m": dist_hydro,
        "dist_to_coast_m": dist_coast,
        "dist_to_water_m": dist_water,
    })

    out_path = Path("processed") / city / "priors" / "building_water_proximity_v3.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out.to_parquet(out_path, index=False)

    print(f"[saved] {out_path}")


def main():
    for city in CITIES:
        process_city(city)


if __name__ == "__main__":
    main()