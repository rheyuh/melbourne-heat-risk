"""Read-only checks on the raw data files (step 1.3, Inspect the sources).

Nothing here writes to the database or changes a file; each check only prints.
Run one check at a time from backend/:

    uv run python inspect_sources.py heat        # layer, columns, types, value ranges
    uv run python inspect_sources.py heat_more   # LGAs, negative UHI, coverage of 2021 SA2s
    uv run python inspect_sources.py seifa       # sheet layout, code rows, missing scores
    uv run python inspect_sources.py crossings   # mesh blocks that cross a 2021 SA2 edge
"""

import sys

import geopandas as gpd
import pandas as pd

from config import (
    GREATER_MELBOURNE,
    HEAT_VEG_FILE,
    HEAT_VEG_LAYER,
    SA2_FILE,
    SA2_LAYER,
    SEIFA_FILE,
    SEIFA_SHEET,
)

# Areas must be measured in metres, not degrees, so overlay work uses
# GDA2020 / MGA zone 55 (EPSG:7855), the flat projection that covers Melbourne.
METRES_CRS = 7855

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)


def read_melbourne_sa2s(columns):
    """Greater Melbourne SA2s with a shape, in metres."""
    sa2 = gpd.read_file(SA2_FILE, layer=SA2_LAYER, columns=columns + ["GCCSA_CODE_2021"])
    is_melbourne = sa2["GCCSA_CODE_2021"] == GREATER_MELBOURNE
    has_shape = sa2.geometry.notna()
    return sa2[is_melbourne & has_shape].to_crs(METRES_CRS)


def inspect_heat():
    """Layer name, row count, CRS, shape types, columns and value ranges."""
    layers = gpd.list_layers(HEAT_VEG_FILE)
    print(layers)

    heat = gpd.read_file(HEAT_VEG_FILE, layer=HEAT_VEG_LAYER)
    attributes = heat.drop(columns="geometry")

    print(f"\nrows: {len(heat)}")
    print(f"CRS: {heat.crs.to_string()}")
    print(f"shape types: {heat.geom_type.value_counts().to_dict()}")
    print(f"bounds (west, south, east, north): {heat.total_bounds.round(4)}")
    print(f"missing shapes: {heat.geometry.isna().sum()}, empty shapes: {heat.geometry.is_empty.sum()}")

    print("\ncolumns and types:")
    print(heat.dtypes.to_string())

    print("\nfirst 3 rows (one column per line):")
    print(attributes.head(3).T.to_string())

    print("\nnumber columns: count, mean, min, max ...")
    print(attributes.describe().T.to_string())


def inspect_heat_more():
    """Area codes, negative heat values, and how much of each 2021 SA2 the heat data covers."""
    heat = gpd.read_file(HEAT_VEG_FILE, layer=HEAT_VEG_LAYER)

    print(f"GCC_CODE16 values: {heat['GCC_CODE16'].value_counts().to_dict()}")
    print(f"LGAs: {heat['LGA'].nunique()}")
    print(f"2016 SA2s: {heat['SA2_MAIN16'].nunique()}")
    print(f"MB_CODE16 unique: {heat['MB_CODE16'].is_unique}")
    print(f"UHI18_M below 0: {(heat['UHI18_M'] < 0).sum()}")
    print(f"missing values (all columns): {heat.isna().sum().sum()}")

    # Coverage: cut the mesh blocks to each SA2, then compare covered area with SA2 area
    melbourne = read_melbourne_sa2s(["SA2_CODE_2021", "SA2_NAME_2021"])
    heat_metres = heat[["geometry"]].to_crs(METRES_CRS)

    pieces = gpd.overlay(melbourne, heat_metres, how="intersection", keep_geom_type=True)
    covered_area = pieces.dissolve("SA2_CODE_2021").area

    melbourne = melbourne.set_index("SA2_CODE_2021")
    melbourne["share"] = (covered_area / melbourne.area).reindex(melbourne.index).fillna(0)

    none = melbourne["share"] < 0.01
    full = melbourne["share"] >= 0.95
    partial = ~none & ~full
    print(f"\n2021 Melbourne SA2s covered: none (<1%): {none.sum()}, partial: {partial.sum()}, almost full (95%+): {full.sum()}")

    not_full = melbourne[~full].sort_values("share")
    print(not_full[["SA2_NAME_2021", "share"]].round(2).to_string())


def inspect_seifa():
    """Sheet names, header rows, code rows, and which SA2s have no score."""
    workbook = pd.ExcelFile(SEIFA_FILE)
    print(f"sheets: {workbook.sheet_names}")

    print("\nTable 2, top rows as they are in the sheet:")
    top_rows = pd.read_excel(SEIFA_FILE, sheet_name=SEIFA_SHEET, header=None, nrows=9)
    print(top_rows.to_string())

    table = pd.read_excel(SEIFA_FILE, sheet_name=SEIFA_SHEET, header=None, skiprows=6)
    print(f"\nrows below the header: {len(table)}")
    print("last rows (first 4 columns):")
    print(table.tail(6).iloc[:, :4].to_string())

    print(f"\ncolumn 0 type as read: {table[0].dtype}")
    print(f"Python types in column 0: {table[0].map(type).value_counts().to_dict()}")

    codes = table[0].astype(str).str.strip()
    is_sa2_code = codes.str.fullmatch(r"\d{9}")
    print(f"rows with a 9-digit code: {is_sa2_code.sum()}")

    seifa = table[is_sa2_code].copy()
    seifa["code"] = codes[is_sa2_code]
    score = pd.to_numeric(seifa[3], errors="coerce")
    print(f"code rows with no score: {score.isna().sum()}")

    # Compare SEIFA codes with ASGS codes (attributes only, no shapes needed)
    sa2 = gpd.read_file(SA2_FILE, layer=SA2_LAYER, ignore_geometry=True)
    asgs_codes = set(sa2["SA2_CODE_2021"])
    seifa_codes = set(seifa["code"])
    print(f"\nSEIFA codes not in ASGS: {len(seifa_codes - asgs_codes)}")
    print(f"ASGS codes not in SEIFA: {len(asgs_codes - seifa_codes)}")

    melbourne_codes = set(sa2.loc[sa2["GCCSA_CODE_2021"] == GREATER_MELBOURNE, "SA2_CODE_2021"])
    scored_codes = set(seifa.loc[score.notna(), "code"])
    print(f"Melbourne SA2s without a score: {len(melbourne_codes - scored_codes)}")


def inspect_crossings():
    """Mesh blocks (2016) that are split across more than one 2021 SA2."""
    heat = gpd.read_file(HEAT_VEG_FILE, layer=HEAT_VEG_LAYER, columns=["MB_CODE16", "SA2_NAME16"])
    heat = heat.to_crs(METRES_CRS)
    heat["mb_area"] = heat.area

    melbourne = read_melbourne_sa2s(["SA2_CODE_2021", "SA2_NAME_2021", "CHANGE_LABEL_2021"])

    # Cut every mesh block along SA2 edges; a block inside one SA2 gives one piece
    pieces = gpd.overlay(heat, melbourne, how="intersection", keep_geom_type=True)
    pieces["share"] = pieces.area / pieces["mb_area"]
    pieces = pieces[pieces["share"] > 0.001]   # ignore slivers from edges that almost line up

    pieces_per_block = pieces.groupby("MB_CODE16").size()
    crossing_blocks = pieces_per_block[pieces_per_block > 1].index
    print(f"mesh blocks: {len(heat)}")
    print(f"inside one SA2: {(pieces_per_block == 1).sum()}")
    print(f"cross 2+ SA2s: {len(crossing_blocks)}")

    # How big is the smaller piece? 1% is a wobble; 10% or more is a real split
    smaller_piece = pieces[pieces["MB_CODE16"].isin(crossing_blocks)].groupby("MB_CODE16")["share"].min()
    print(f"smaller piece 10%+ of the block: {(smaller_piece >= 0.10).sum()}")
    print(f"smaller piece 30%+ of the block: {(smaller_piece >= 0.30).sum()}")

    real_splits = pieces[pieces["MB_CODE16"].isin(smaller_piece[smaller_piece >= 0.10].index)]
    print("\nSA2s with the most real splits:")
    per_sa2 = real_splits.groupby(["SA2_NAME_2021", "CHANGE_LABEL_2021"]).size()
    print(per_sa2.sort_values(ascending=False).head(12).to_string())

    print("\nexample mesh blocks:")
    examples = real_splits.sort_values("share").drop_duplicates("MB_CODE16").head(5)["MB_CODE16"]
    example_pieces = pieces[pieces["MB_CODE16"].isin(examples)]
    print(example_pieces[["MB_CODE16", "SA2_NAME16", "SA2_NAME_2021", "share"]].round(2).to_string(index=False))


CHECKS = {
    "heat": inspect_heat,
    "heat_more": inspect_heat_more,
    "seifa": inspect_seifa,
    "crossings": inspect_crossings,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        print(f"Usage: uv run python inspect_sources.py [{' | '.join(CHECKS)}]")
        sys.exit(1)

    check = CHECKS[sys.argv[1]]
    check()
