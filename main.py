import plotly.graph_objects as go
import pandas as pd
import json
import geopandas as gpd
import numpy as np
from datetime import datetime

def numpy_to_python(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")
    return obj

def create_dc_poi_map():
    # Load the weather data to get DC coordinates
    weather_df = pd.read_csv('datasets/weather.csv')
    
    dc_lat = weather_df['lat'].iloc[0]  
    dc_lon = weather_df['lon'].iloc[0]  
    
    fig = go.Figure()
    
    bike_data_by_date = {}
    museum_indices = []
    university_indices = []
    memorial_indices = []
    grid_indices = []
    weather_data_by_date = {}
    
    # Process weather data
    try:
        weather_df['date'] = weather_df['dt_iso'].str.split(' ').str[0]
        weather_df['time'] = weather_df['dt_iso'].str.split(' ').str[1].str.split(' ').str[0]
        
        weather_df['hour'] = pd.to_datetime(weather_df['time'], format='%H:%M:%S').dt.hour
        
        for date in weather_df['date'].unique():
            day_data = weather_df[weather_df['date'] == date].copy()
            
            day_data['datetime'] = pd.to_datetime(day_data['time'], format='%H:%M:%S')
            day_data = day_data.sort_values('datetime')
            
            hours = []
            temp_data = []
            feels_like_data = []
            hourly_weather = {} 
            
            for _, row in day_data.iterrows():
                hour = int(row['hour'])
                hours.append(hour)
                temp_data.append(float(row['temp']))
                feels_like_data.append(float(row['feels_like']))
                

                if 'weather_description' in row:
                    hourly_weather[str(hour)] = str(row['weather_description'])
                elif 'weather_main' in row:
                    hourly_weather[str(hour)] = str(row['weather_main'])
            

            most_common_weather = "N/A"
            if 'weather_description' in day_data.columns:
                most_common_weather = str(day_data['weather_description'].value_counts().index[0])
            elif 'weather_main' in day_data.columns:
                most_common_weather = str(day_data['weather_main'].value_counts().index[0])
            

            weather_data_by_date[date] = {
                'hours': hours,
                'temp': temp_data,
                'feels_like': feels_like_data,
                'min_temp': float(day_data['temp'].min()),
                'max_temp': float(day_data['temp'].max()),
                'avg_temp': float(day_data['temp'].mean()),
                'humidity': float(day_data['humidity'].mean()),
                'wind_speed': float(day_data['wind_speed'].mean()),
                'weather_main': most_common_weather,
                'hourly_weather': hourly_weather 
            }
        
        print(f"Processed weather data for {len(weather_data_by_date)} dates")
        sample_date = list(weather_data_by_date.keys())[0]
        print(f"Sample weather data structure for {sample_date}:", weather_data_by_date[sample_date])
    except Exception as e:
        print(f"Error processing weather data: {e}")
        print("Continuing without weather data...")
    
    # LAYER: Bike Data
    try:
        bike_df = pd.read_csv('datasets/202501-capitalbikeshare-tripdata.csv')
        print(f"Loaded bike data with {len(bike_df)} rows")
        
        # Convert to datetime
        try:
            bike_df['started_at_dt'] = pd.to_datetime(bike_df['started_at'])
            bike_df['date'] = bike_df['started_at_dt'].dt.strftime('%Y-%m-%d')
            bike_df['hour'] = bike_df['started_at_dt'].dt.hour  # Extract hour for time slider
        except:
            print("Trying mixed format for dates...")
            bike_df['started_at_dt'] = pd.to_datetime(bike_df['started_at'], format='mixed')
            bike_df['date'] = bike_df['started_at_dt'].dt.strftime('%Y-%m-%d')
            bike_df['hour'] = bike_df['started_at_dt'].dt.hour  # Extract hour for time slider

        unique_dates = sorted(bike_df['date'].unique())
        print(f"Found {len(unique_dates)} unique dates in bike data")
        
        for date in unique_dates:
            date_df = bike_df[bike_df['date'] == date]
            
            # Create hourly bike data for time slider
            hourly_data = {}
            for hour in range(24):
                hour_df = date_df[date_df['hour'] == hour]
                hourly_data[hour] = {
                    'count': len(hour_df),
                    'lat': hour_df['start_lat'].tolist(),
                    'lng': hour_df['start_lng'].tolist()
                }
            
            bike_data_by_date[date] = {
                'count': len(date_df),
                'lat': date_df['start_lat'].tolist(),
                'lng': date_df['start_lng'].tolist(),
                'hourly': hourly_data  # Add hourly data
            }
        
        bike_trace_index = len(fig.data)
        fig.add_trace(go.Scattermapbox(
            lat=[],
            lon=[],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='Bike Data',
            visible=False
        ))
        
        print("Prepared bike data by date and hour")
    except Exception as e:
        print(f"Error loading bike data: {e}")
        print("Continuing without bike layer...")
    
    # Resto do código permanece o mesmo
    
    # LAYER: Points of Interest (POI)
    try:
        world = gpd.read_file('datasets/pois/gis_osm_pois_free_1.shp')
        poi_categories = ['museum', 'university', 'memorial','attraction', 'cafe', 'restaurant', 'bar', 'pub', 'nightclub']
 
        filtered_world = world[world['fclass'].isin(poi_categories)].copy()  

        filtered_world.loc[:, 'name'] = filtered_world['name'].fillna('Unknown')
 
        filtered_world.loc[:, 'lat'] = filtered_world.geometry.y
 
        filtered_world.loc[:, 'lon'] = filtered_world.geometry.x
 
        for category in poi_categories:
            category_df = filtered_world[filtered_world['fclass'] == category].copy()
            # Define color based on category
            if category == 'museum':
                color = 'darkblue'
            elif category == 'university':
                color = 'darkgreen'
            elif category == 'memorial':
                color = 'purple'
            elif category == 'attraction':
                color = 'orange'
            elif category == 'cafe':
                color = 'brown'
            elif category == 'restaurant':
                color = 'teal'
            elif category == 'bar':
                color = 'blue'
            elif category == 'pub':
                color = 'yellow'
            elif category == 'nightclub':
                color = 'pink'
            else:
                color = 'gray'
            fig.add_trace(go.Scattermapbox(
                lat=category_df['lat'].tolist(),
                lon=category_df['lon'].tolist(),  
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=10,
                    color=color,
                    opacity=0.7
                ),
                text=category_df['name'].tolist(),  
                hoverinfo='text',
                hovertemplate='<b>%{text}</b><br>Type: ' + category,
                name=f'{category.capitalize()}s',
                visible=False,  # All layers hidden by default
                legendgroup='POI'
 
            ))
 
        print(f"Successfully loaded {len(filtered_world)} points of interest")
 

 
    except Exception as e:
 
        print(f"Error loading POI data: {e}")
 
        print("Continuing without POI layer...")
    
    # LAYER: Grid Layer
    lat_min, lat_max = dc_lat - 0.5, dc_lat + 0.5
    lon_min, lon_max = dc_lon - 0.5, dc_lon + 0.5
    
    # Grid size 
    grid_size = 0.05  
    
    lat_lines = [lat_min + i * grid_size for i in range(int((lat_max - lat_min) / grid_size) + 1)]
    lon_lines = [lon_min + i * grid_size for i in range(int((lon_max - lon_min) / grid_size) + 1)]
    
    default_grid_color = 'rgba(255,0,0,0.5)' 
    default_grid_width = 0.5
    
    # Add latitude lines (horizontal)
    for lat in lat_lines:
        grid_trace_index = len(fig.data)
        fig.add_trace(go.Scattermapbox(
            lat=[lat, lat],
            lon=[lon_min, lon_max],
            mode='lines',
            line=dict(color=default_grid_color, width=default_grid_width),
            hoverinfo='none',
            showlegend=False,
            visible=False,  # Hidden by default
            name='Grid',
            legendgroup='Grid'
        ))
        grid_indices.append(grid_trace_index)
    
    # Add longitude lines (vertical)
    for lon in lon_lines:
        grid_trace_index = len(fig.data)
        fig.add_trace(go.Scattermapbox(
            lat=[lat_min, lat_max],
            lon=[lon, lon],
            mode='lines',
            line=dict(color=default_grid_color, width=default_grid_width),
            hoverinfo='none',
            showlegend=False,
            visible=False,  # Hidden by default
            name='Grid',
            legendgroup='Grid'
        ))
        grid_indices.append(grid_trace_index)
    
    print(f"Added grid with {len(grid_indices)} lines")
    
    # Update layout
    fig.update_layout(
        title=None,
        mapbox=dict(
            accesstoken="pk.eyJ1Ijoiemhla2Fwb2wiLCJhIjoiQmtWbXh0YyJ9.pt2Y2ymqvDdgrIKpNAx8nQ",
            #style="mapbox://styles/zhekapol/cl0cj5492001j14rm8jvqakk7", 
            style="light",
            center=dict(lat=dc_lat, lon=dc_lon),
            zoom=10
        ),
        height=700,
        width=1000,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    

    config = {
        'displayModeBar': False,
        'scrollZoom': True
    }
    
    # Create indices object to pass to HTML
    layer_indices = {
        'bike_placeholder': bike_trace_index,
        'museum': museum_indices,
        'university': university_indices,
        'memorial': memorial_indices,
        'grid': {
            'indices': grid_indices,
            'default_color': default_grid_color,
            'default_width': default_grid_width
        }
    }
    
    try:
        # Convert to JSON
        plotly_json = json.dumps(fig.to_dict(), default=numpy_to_python)
        indices_json = json.dumps(layer_indices)
        bike_data_json = json.dumps(bike_data_by_date)
        weather_data_json = json.dumps(weather_data_by_date, default=numpy_to_python)
        config_json = json.dumps(config)
        
        # Create HTML content
        with open('main.html', 'r') as template_file:
            html_template = template_file.read()
        
        html_content = html_template.replace('{plotly_json}', plotly_json)
        html_content = html_content.replace('{layer_indices}', indices_json)
        html_content = html_content.replace('{bike_data_json}', bike_data_json)
        html_content = html_content.replace('{weather_data_json}', weather_data_json)
        html_content = html_content.replace('{config_json}', config_json)
        
        # Write HTML file
        with open('index.html', 'w') as f:
            f.write(html_content)
        
        print("Map created successfully. Check index.html")
        
    except Exception as e:
        print(f"Error creating HTML: {e}")
        fig.write_html("fallback_map.html", config=config)
        print("Created fallback map instead.")
    
    return fig

if __name__ == "__main__":
    create_dc_poi_map()