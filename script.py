import pandas as pd
import fiona
from shapely.geometry import shape, MultiPolygon, Polygon

# Define file paths
mid_file_path = "./CADPLAN.mid"
mif_file_path = "./CADPLAN.mif"


def count_contours(geometry):
    """
    Count the total number of contours (external and internal) in a Polygon or MultiPolygon.

    Parameters:
    geometry (shapely.geometry.Polygon or shapely.geometry.MultiPolygon): The geometry object.

    Returns:
    int: The total number of contours.
    """
    total_contours = 0

    if isinstance(geometry, Polygon):
        # External contour plus internal contours
        total_contours = 1 + len(geometry.interiors)

    elif isinstance(geometry, MultiPolygon):
        # External contour plus internal contours for each polygon
        for polygon in geometry.geoms:
            total_contours += 1 + len(polygon.interiors)

    return total_contours


# Read the MIF file using Fiona
with fiona.open(mif_file_path, "r") as mif_file:
    # Extract the schema (column names and types)
    schema = mif_file.schema
    crs = mif_file.crs

    columns = list(schema["properties"].keys())

    # Extract data
    data = []
    for feature in mif_file:
        properties = feature["properties"]
        geometry = shape(feature["geometry"])
        properties["geometry"] = geometry
        data.append(properties)


def convert_to_mif_format(geometry):
    """
    Convert a geometry object to MIF format.

    Parameters:
    geometry (shapely.geometry.Polygon or shapely.geometry.MultiPolygon): The geometry object.

    Returns:
    str: The MIF formatted string.
    """
    mif_coords = ""
    if isinstance(geometry, Polygon):
        polygons = [geometry]

    elif isinstance(geometry, MultiPolygon):
        polygons = list(geometry.geoms)
    else:
        return None

    mif_coords += f"Region {count_contours(geometry)}\n"
    for polygon in polygons:
        coords = list(polygon.exterior.coords)
        mif_coords += f"{len(coords)}\n"
        for coord in coords:
            mif_coords += f"{coord[0]} {coord[1]}\n"

        for interior in polygon.interiors:
            interior_coords = list(interior.coords)
            mif_coords += f"{len(interior_coords)}\n"
            for coord in interior_coords:
                mif_coords += f"{coord[0]} {coord[1]}\n"

    return f'{mif_coords.replace(", ","")}\n'


# Create DataFrame
df = pd.DataFrame(data, columns=columns + ["geometry"])

# Apply the conversion function to each geometry in the DataFrame
df["mif_format_geometry"] = df["geometry"].apply(convert_to_mif_format)

# Style the DataFrame
df.style.set_table_styles(
    [
        {
            "selector": "thead th",
            "props": [("background-color", "lightgrey"), ("font-weight", "bold")],
        },
        {"selector": "tbody td", "props": [("border", "1px solid black")]},
    ]
).set_caption("Beautiful DataFrame")


def remove_after_bracket(name):
    """
    Remove text after the bracket in a string.

    Parameters:
    name (str): The input string.

    Returns:
    str: The modified string.
    """
    return name.split("(")[0].strip()


# Apply the function to the 'MARKING' column
df["origin"] = df["MARKING"].apply(remove_after_bracket)


def create_mif_mid_files(df, key_field):
    """
    Create MIF and MID files for each row in the DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame.
    key_field (str): The key field for naming the files.
    """
    for index, row in df.iterrows():
        mif_filename = f'./new/{index + 1}_{row[key_field].replace(":", "_")}.mif'

        with open(mif_filename, "w") as mif_file:
            # Write the MIF header
            mif_file.write("Version 300\n")
            mif_file.write('Charset "WindowsLatin1"\n')
            mif_file.write('Delimiter ","\n')
            mif_file.write('CoordSys Nonearth Units "m" Bounds\n')
            mif_file.write("Columns " + str(len(columns)) + "\n")
            for col in columns:
                mif_file.write(f"  {col} Char(254)\n")
            mif_file.write("Data\n")

            # Write the geometry
            mif_file.write((row["mif_format_geometry"] + "\n").replace(", ", ""))


# Group DataFrame by 'origin' and aggregate
grouped_df = (
    df.groupby("origin")
    .agg(
        {
            "mif_format_geometry": ", ".join,  # Concatenate text values
            "MARKING": "count",  # Count the number of rows
        }
    )
    .rename(columns={"MARKING": "count"})
    .reset_index()
)

# Create MIF and MID files for the grouped DataFrame
create_mif_mid_files(grouped_df, "origin")

# Convert DataFrame to HTML and save to file
html_table = df.to_html(classes="table table-striped")
with open("table.html", "w") as f:
    f.write(html_table)
