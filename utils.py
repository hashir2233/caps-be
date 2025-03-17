import pandas as pd
import numpy as np
from scipy import stats
import datetime
from sklearn.cluster import DBSCAN

def identify_crime_hotspots(df, eps=0.005, min_samples=3):
    """
    Identify crime hotspots using DBSCAN clustering on geographical coordinates
    
    Parameters:
    - eps: The maximum distance between two samples to be considered in the same neighborhood
    - min_samples: The number of samples in a neighborhood for a point to be considered a core point
    
    Returns:
    - DataFrame with cluster labels and centroid information
    """
    # Extract coordinates
    coords = df[['Latitude', 'Longitude']].values
    
    # Apply DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    
    # Add cluster labels to the original dataframe
    df_clusters = df.copy()
    df_clusters['cluster'] = clustering.labels_
    
    # Find cluster centroids and count points
    centroids = []
    for cluster_id in sorted(set(clustering.labels_)):
        if cluster_id == -1:  # Skip noise points
            continue
            
        # Get points in this cluster
        mask = df_clusters['cluster'] == cluster_id
        cluster_points = df_clusters[mask]
        
        # Calculate centroid
        centroid_lat = cluster_points['Latitude'].mean()
        centroid_lon = cluster_points['Longitude'].mean()
        count = len(cluster_points)
        
        # Find most common crime type
        most_common_crime = cluster_points['Crime_Type'].value_counts().idxmax()
        
        centroids.append({
            'cluster_id': cluster_id,
            'centroid_lat': centroid_lat,
            'centroid_lon': centroid_lon,
            'point_count': count,
            'most_common_crime': most_common_crime,
            'neighborhoods': ', '.join(cluster_points['Neighborhood'].unique())
        })
    
    # Create dataframe with centroid information
    centroids_df = pd.DataFrame(centroids)
    
    return df_clusters, centroids_df

def find_temporal_patterns(df):
    """
    Identify temporal patterns in crime data
    
    Returns:
    - Dictionary with various temporal pattern analyses
    """
    patterns = {}
    
    # Analyze by month
    monthly_counts = df.groupby(['Month', 'Crime_Type']).size().reset_index(name='count')
    patterns['monthly'] = monthly_counts.pivot(index='Month', columns='Crime_Type', values='count').fillna(0)
    
    # Analyze by day of week
    dow_counts = df.groupby(['Day_of_Week', 'Crime_Type']).size().reset_index(name='count')
    patterns['day_of_week'] = dow_counts.pivot(index='Day_of_Week', columns='Crime_Type', values='count').fillna(0)
    
    # Order days of week correctly
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if 'day_of_week' in patterns and all(day in patterns['day_of_week'].index for day in day_order):
        patterns['day_of_week'] = patterns['day_of_week'].reindex(day_order)
    
    # Analyze by time of day
    tod_counts = df.groupby(['Time_of_Day', 'Crime_Type']).size().reset_index(name='count')
    patterns['time_of_day'] = tod_counts.pivot(index='Time_of_Day', columns='Crime_Type', values='count').fillna(0)
    
    # Order time of day correctly
    time_order = ['Morning', 'Afternoon', 'Evening', 'Night']
    if 'time_of_day' in patterns and all(time in patterns['time_of_day'].index for time in time_order):
        patterns['time_of_day'] = patterns['time_of_day'].reindex(time_order)
    
    return patterns

def analyze_environmental_factors(df):
    """
    Analyze how environmental factors relate to crime
    
    Returns:
    - Dictionary with environmental factor analyses
    """
    analyses = {}
    
    # Weather analysis
    weather_crime = pd.crosstab(df['Weather'], df['Crime_Type'])
    analyses['weather_crime'] = weather_crime
    
    # Temperature analysis (binned)
    df['Temp_Bin'] = pd.cut(df['Temperature'], bins=[-10, 0, 10, 20, 30, 45], 
                            labels=['Very Cold', 'Cold', 'Moderate', 'Warm', 'Hot'])
    temp_crime = pd.crosstab(df['Temp_Bin'], df['Crime_Type'])
    analyses['temperature_crime'] = temp_crime
    
    # Lighting analysis
    light_crime = pd.crosstab(df['Lighting'], df['Crime_Type'])
    analyses['lighting_crime'] = light_crime
    
    return analyses

def analyze_socioeconomic_factors(df):
    """
    Analyze how socioeconomic factors relate to crime
    
    Returns:
    - Dictionary with socioeconomic factor analyses
    """
    analyses = {}
    
    # Create income bins
    df['Income_Bin'] = pd.qcut(df['Average_Income'], 4, 
                               labels=['Low Income', 'Lower-Middle Income', 
                                      'Upper-Middle Income', 'High Income'])
    income_crime = pd.crosstab(df['Income_Bin'], df['Crime_Type'])
    analyses['income_crime'] = income_crime
    
    # Create unemployment bins
    df['Unemployment_Bin'] = pd.qcut(df['Unemployment_Rate'], 4,
                                     labels=['Low', 'Medium-Low', 'Medium-High', 'High'])
    unemployment_crime = pd.crosstab(df['Unemployment_Bin'], df['Crime_Type'])
    analyses['unemployment_crime'] = unemployment_crime
    
    # Create population density bins
    df['Density_Bin'] = pd.qcut(df['Population_Density'], 4,
                               labels=['Low Density', 'Medium-Low Density', 
                                      'Medium-High Density', 'High Density'])
    density_crime = pd.crosstab(df['Density_Bin'], df['Crime_Type'])
    analyses['density_crime'] = density_crime
    
    # Calculate correlation coefficients
    socio_factors = ['Population_Density', 'Average_Income', 'Unemployment_Rate']
    corr_data = []
    
    for crime_type in df['Crime_Type'].unique():
        crime_df = df[df['Crime_Type'] == crime_type]
        
        for factor in socio_factors:
            correlation, p_value = stats.pointbiserialr(
                df['Crime_Type'] == crime_type, 
                df[factor]
            )
            
            corr_data.append({
                'Crime_Type': crime_type,
                'Factor': factor,
                'Correlation': correlation,
                'P_Value': p_value,
                'Significant': p_value < 0.05
            })
    
    analyses['correlations'] = pd.DataFrame(corr_data)
    
    return analyses