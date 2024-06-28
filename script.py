import pandas as pd
import fiona
from shapely.geometry import shape

# Define file paths
mid_file_path = './CADPLAN.mid'
mif_file_path = './CADPLAN.mif'

# Read the MIF file using Fiona
with fiona.open(mif_file_path, 'r') as mif_file:
    # Extract the schema (column names and types)
    schema = mif_file.schema
    crs = mif_file.crs
    print(schema)
    columns = list(schema['properties'].keys())
    print(columns)
    print(crs)
    # Extract data
    data = []
    for feature in mif_file:
        properties = feature['properties']
        geometry = shape(feature['geometry'])
        properties['geometry'] = geometry
        data.append(properties)

# Create DataFrame
df = pd.DataFrame(data, columns=columns + ['geometry'])



 
# Apply the conversion function to each geometry in the DataFrame
df['mif_format_geometry'] = df['geometry'].apply(convert_to_mif_format)
 
df.style.set_table_styles(
    [
        {'selector': 'thead th', 'props': [('background-color', 'lightgrey'), ('font-weight', 'bold')]},
        {'selector': 'tbody td', 'props': [('border', '1px solid black')]}
    ]
).set_caption('Beautiful DataFrame')


def remove_after_bracket(name):
    return name.split('(')[0].strip()

# Применение функции к столбцу name
df['origin'] = df['MARKING'].apply(remove_after_bracket)


def create_mif_mid_files(df,key_field):
    for index, row in df.iterrows():
        mif_filename = f'./new/{index + 1}_{row[key_field].replace(":","_")}.mif'
        print(mif_filename)
        #mid_filename = f'./new/{index + 1}_{row[key_field].replace(":","_")}.mid'
       
        with open(mif_filename, 'w') as mif_file:
            # Write the MIF header
            mif_file.write('Version 300\n')
            mif_file.write('Charset "WindowsLatin1"\n')
            mif_file.write('Delimiter ","\n')
            mif_file.write('CoordSys Nonearth Units "m" Bounds\n')
            mif_file.write('Columns ' + str(len(columns)) + '\n')
            for col in columns:
                mif_file.write(f'  {col} Char(254)\n')
            mif_file.write('Data\n')

            # Write the geometry
            mif_file.write(row['mif_format_geometry'] + '\n')

        #with open(mid_filename, 'w', encoding='utf-8') as mid_file:
            # Write the attribute data
            #mid_file.write(','.join([str(row[col]) for col in columns]) + '\n')

# Create MIF and MID files for each row in DataFrame
#create_mif_mid_files(df)

# grouped_df = df.groupby('origin').size().reset_index(name='count')


grouped_df = df.groupby('origin').agg({
    'mif_format_geometry': ', '.join,  # Объединение текстовых значений
    #'value': 'sum',     # Суммирование числовых значений (пример)
    'MARKING': 'count'  # Подсчет количества строк
}).rename(columns={'MARKING': 'count'}).reset_index()
print(grouped_df.head())
create_mif_mid_files(grouped_df,'origin')

html_table = grouped_df.to_html(classes='table table-striped')
with open('table.html', 'w') as f:
    f.write(html_table)