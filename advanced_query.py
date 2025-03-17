import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sentence_transformers import SentenceTransformer
from main import load_and_preprocess_data, engineer_features, generate_embeddings, setup_chroma_db, generate_contextual_response
from gemini_integration import setup_gemini

def advanced_query_interface(df, collections, gemini_model=None):
    """
    Advanced query interface with specialized crime analysis capabilities
    """
    print("\n" + "="*50)
    print("ADVANCED CRIME ANALYSIS INTERFACE")
    print("="*50)
    
    # Initialize Gemini model if not provided
    if gemini_model is None:
        gemini_model = setup_gemini(api_key=os.environ.get("GEMINI_API_KEY"))
    
    while True:
        print("\nSelect analysis type:")
        print("1. Crime Hotspot Identification")
        print("2. Temporal Pattern Analysis")
        print("3. Environmental Factor Analysis")
        print("4. Socioeconomic Factor Analysis")
        print("5. Multi-factor Crime Query")
        print("6. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            crime_hotspot_analysis(df, collections, gemini_model)
        elif choice == '2':
            temporal_pattern_analysis(df, collections, gemini_model)
        elif choice == '3':
            environmental_factor_analysis(df, collections, gemini_model)
        elif choice == '4':
            socioeconomic_analysis(df, collections, gemini_model)
        elif choice == '5':
            multi_factor_query(df, collections, gemini_model)
        elif choice == '6':
            print("\nReturning to main menu...")
            break
        else:
            print("\nInvalid choice. Please try again.")

def crime_hotspot_analysis(df, collections, gemini_model=None):
    """
    Identify and analyze crime hotspots
    """
    print("\n" + "="*30)
    print("CRIME HOTSPOT ANALYSIS")
    print("="*30)
    
    # Get neighborhood filter if desired
    print("\nNeighborhoods in dataset:")
    neighborhoods = sorted(df['Neighborhood'].unique())
    for i, neighborhood in enumerate(neighborhoods):
        print(f"{i+1}. {neighborhood}")
    print(f"{len(neighborhoods)+1}. All neighborhoods")
    
    choice = input("\nSelect neighborhood number (or 'all'): ")
    if choice.lower() == 'all' or choice == str(len(neighborhoods)+1):
        filtered_df = df.copy()
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(neighborhoods):
                filtered_df = df[df['Neighborhood'] == neighborhoods[idx]].copy()
            else:
                print("Invalid selection. Using all neighborhoods.")
                filtered_df = df.copy()
        except:
            print("Invalid selection. Using all neighborhoods.")
            filtered_df = df.copy()
    
    # Count crimes by location
    crime_counts = filtered_df.groupby(['Latitude', 'Longitude', 'Neighborhood']).size().reset_index(name='Crime_Count')
    crime_counts = crime_counts.sort_values('Crime_Count', ascending=False)
    
    print("\nTop 5 Crime Hotspots:")
    for i, (_, row) in enumerate(crime_counts.head(5).iterrows()):
        print(f"{i+1}. {row['Neighborhood']} at coordinates ({row['Latitude']}, {row['Longitude']}): {row['Crime_Count']} crimes")
    
    # Visualize if possible
    try:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(data=crime_counts, x='Longitude', y='Latitude', size='Crime_Count', 
                        hue='Neighborhood', sizes=(20, 200), alpha=0.7)
        plt.title('Crime Hotspots Map')
        plt.tight_layout()
        plt.savefig('output/crime_hotspots.png')
        print("\nCrime hotspot map saved to output/crime_hotspots.png")
    except Exception as e:
        print(f"\nVisualization error: {e}")
    
    # Generate contextual queries
    if gemini_model:
        print("\nGenerating contextual analysis...")
        top_hotspots = crime_counts.head(3)
        for _, hotspot in top_hotspots.iterrows():
            # Find crimes at this location
            location_crimes = filtered_df[
                (filtered_df['Latitude'] == hotspot['Latitude']) & 
                (filtered_df['Longitude'] == hotspot['Longitude'])
            ]
            
            query = f"Analyze crime patterns at coordinates ({hotspot['Latitude']}, {hotspot['Longitude']}) in {hotspot['Neighborhood']}."
            response = generate_contextual_response(query, location_crimes, model=gemini_model)
            
            print(f"\n--- Analysis for hotspot in {hotspot['Neighborhood']} ---")
            print(response)
            print("---" * 10)
    
    input("\nPress Enter to continue...")

def temporal_pattern_analysis(df, collections, gemini_model=None):
    """
    Analyze temporal patterns in crime data
    """
    print("\n" + "="*30)
    print("TEMPORAL PATTERN ANALYSIS")
    print("="*30)
    
    print("\nSelect time dimension to analyze:")
    print("1. Month")
    print("2. Day of Week")
    print("3. Time of Day")
    print("4. Month + Time of Day")
    print("5. Day of Week + Time of Day")
    
    choice = input("\nEnter choice (1-5): ")
    
    # Allow optional crime type filter
    print("\nFilter by crime type?")
    print("1. All crime types")
    crime_types = sorted(df['Crime_Type'].unique())
    for i, crime in enumerate(crime_types):
        print(f"{i+2}. {crime}")
    
    crime_choice = input("\nEnter choice: ")
    if crime_choice == '1':
        filtered_df = df.copy()
        crime_filter = "all crime types"
    else:
        try:
            crime_idx = int(crime_choice) - 2
            if 0 <= crime_idx < len(crime_types):
                crime_type = crime_types[crime_idx]
                filtered_df = df[df['Crime_Type'] == crime_type].copy()
                crime_filter = crime_type
            else:
                filtered_df = df.copy()
                crime_filter = "all crime types"
                print("Invalid selection. Using all crime types.")
        except:
            filtered_df = df.copy()
            crime_filter = "all crime types"
            print("Invalid selection. Using all crime types.")
    
    # Perform temporal analysis based on choice
    if choice == '1':  # Month
        temporal_counts = filtered_df.groupby('Month').size().reset_index(name='Crime_Count')
        # Get proper month order
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        temporal_counts['Month_Num'] = temporal_counts['Month'].map(lambda x: month_order.index(x))
        temporal_counts = temporal_counts.sort_values('Month_Num')
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=temporal_counts, x='Month', y='Crime_Count', order=month_order)
        plt.title(f'Crime Frequency by Month ({crime_filter})')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('output/crime_by_month.png')
        print("\nTemporal analysis chart saved to output/crime_by_month.png")
        
        # Get summary
        max_month = temporal_counts.loc[temporal_counts['Crime_Count'].idxmax()]
        print(f"\nMonth with highest crime rate: {max_month['Month']} with {max_month['Crime_Count']} crimes")
        
    elif choice == '2':  # Day of Week
        temporal_counts = filtered_df.groupby('Day_of_Week').size().reset_index(name='Crime_Count')
        # Get proper day order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        temporal_counts['Day_Num'] = temporal_counts['Day_of_Week'].map(lambda x: day_order.index(x))
        temporal_counts = temporal_counts.sort_values('Day_Num')
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=temporal_counts, x='Day_of_Week', y='Crime_Count', order=day_order)
        plt.title(f'Crime Frequency by Day of Week ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_day.png')
        print("\nTemporal analysis chart saved to output/crime_by_day.png")
        
        # Get summary
        max_day = temporal_counts.loc[temporal_counts['Crime_Count'].idxmax()]
        print(f"\nDay with highest crime rate: {max_day['Day_of_Week']} with {max_day['Crime_Count']} crimes")
        
    elif choice == '3':  # Time of Day
        temporal_counts = filtered_df.groupby('Time_of_Day').size().reset_index(name='Crime_Count')
        # Get proper time order
        time_order = ['Morning', 'Afternoon', 'Evening', 'Night']
        temporal_counts['Time_Num'] = temporal_counts['Time_of_Day'].map(lambda x: time_order.index(x))
        temporal_counts = temporal_counts.sort_values('Time_Num')
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=temporal_counts, x='Time_of_Day', y='Crime_Count', order=time_order)
        plt.title(f'Crime Frequency by Time of Day ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_time.png')
        print("\nTemporal analysis chart saved to output/crime_by_time.png")
        
        # Get summary
        max_time = temporal_counts.loc[temporal_counts['Crime_Count'].idxmax()]
        print(f"\nTime with highest crime rate: {max_time['Time_of_Day']} with {max_time['Crime_Count']} crimes")
        
    elif choice == '4':  # Month + Time of Day
        # Create a crosstab of month vs time of day
        cross_tab = pd.crosstab(filtered_df['Month'], filtered_df['Time_of_Day'])
        
        # Reorder for better visualization
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        time_order = ['Morning', 'Afternoon', 'Evening', 'Night']
        cross_tab = cross_tab.reindex(month_order)[time_order]
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlOrRd')
        plt.title(f'Crime Frequency by Month and Time of Day ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_month_time.png')
        print("\nTemporal analysis chart saved to output/crime_by_month_time.png")
        
        # Get max combination
        max_val = cross_tab.max().max()
        max_loc = [(i, j) for i in cross_tab.index for j in cross_tab.columns if cross_tab.loc[i, j] == max_val]
        print(f"\nHighest crime frequency: {max_val} crimes in {max_loc[0][0]} during {max_loc[0][1]} hours")
        
    elif choice == '5':  # Day of Week + Time of Day
        # Create a crosstab of day vs time of day
        cross_tab = pd.crosstab(filtered_df['Day_of_Week'], filtered_df['Time_of_Day'])
        
        # Reorder for better visualization
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        time_order = ['Morning', 'Afternoon', 'Evening', 'Night']
        cross_tab = cross_tab.reindex(day_order)[time_order]
        
        plt.figure(figsize=(12, 6))
        sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlOrRd')
        plt.title(f'Crime Frequency by Day of Week and Time of Day ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_day_time.png')
        print("\nTemporal analysis chart saved to output/crime_by_day_time.png")
        
        # Get max combination
        max_val = cross_tab.max().max()
        max_loc = [(i, j) for i in cross_tab.index for j in cross_tab.columns if cross_tab.loc[i, j] == max_val]
        print(f"\nHighest crime frequency: {max_val} crimes on {max_loc[0][0]} during {max_loc[0][1]} hours")
    
    # Generate contextual insights if LLM is available
    if gemini_model and filtered_df.shape[0] > 0:
        print("\nGenerating temporal insights...")
        
        # Create a targeted query based on the analysis type
        if choice == '1':  # Month
            query = f"What are the significant temporal patterns for {crime_filter} when analyzing by month of the year?"
        elif choice == '2':  # Day of Week
            query = f"What are the significant temporal patterns for {crime_filter} when analyzing by day of the week?"
        elif choice == '3':  # Time of Day
            query = f"What are the significant temporal patterns for {crime_filter} when analyzing by time of day?"
        elif choice == '4':  # Month + Time of Day
            query = f"What are the significant temporal patterns for {crime_filter} when analyzing by month and time of day combinations?"
        elif choice == '5':  # Day of Week + Time of Day
            query = f"What are the significant temporal patterns for {crime_filter} when analyzing by day of week and time of day combinations?"
        
        # Select a relevant subset of data for the LLM
        if choice in ['1', '2', '3']:
            # Use the top periods with highest crime rates
            top_periods = temporal_counts.nlargest(3, 'Crime_Count')
            if choice == '1':  # Month
                relevant_records = filtered_df[filtered_df['Month'].isin(top_periods['Month'])].head(10)
            elif choice == '2':  # Day of Week
                relevant_records = filtered_df[filtered_df['Day_of_Week'].isin(top_periods['Day_of_Week'])].head(10)
            else:  # Time of Day
                relevant_records = filtered_df[filtered_df['Time_of_Day'].isin(top_periods['Time_of_Day'])].head(10)
        else:
            # For combinations, just take a sample of the data
            relevant_records = filtered_df.sample(min(10, filtered_df.shape[0]))
        
        response = generate_contextual_response(query, relevant_records, model=gemini_model)
        print("\n--- Temporal Pattern Analysis ---")
        print(response)
        print("---" * 10)
        
    input("\nPress Enter to continue...")

def environmental_factor_analysis(df, collections, gemini_model=None):
    """
    Analyze how environmental factors affect crime patterns
    """
    print("\n" + "="*30)
    print("ENVIRONMENTAL FACTOR ANALYSIS")
    print("="*30)
    
    print("\nSelect environmental factor to analyze:")
    print("1. Weather conditions")
    print("2. Temperature ranges")
    print("3. Lighting conditions")
    print("4. Weather + Lighting")
    
    choice = input("\nEnter choice (1-4): ")
    
    # Allow crime type filter
    print("\nFilter by crime type?")
    print("1. All crime types")
    crime_types = sorted(df['Crime_Type'].unique())
    for i, crime in enumerate(crime_types):
        print(f"{i+2}. {crime}")
    
    crime_choice = input("\nEnter choice: ")
    if crime_choice == '1':
        filtered_df = df.copy()
        crime_filter = "all crime types"
    else:
        try:
            crime_idx = int(crime_choice) - 2
            if 0 <= crime_idx < len(crime_types):
                crime_type = crime_types[crime_idx]
                filtered_df = df[df['Crime_Type'] == crime_type].copy()
                crime_filter = crime_type
            else:
                filtered_df = df.copy()
                crime_filter = "all crime types"
                print("Invalid selection. Using all crime types.")
        except Exception as e:
            filtered_df = df.copy()
            crime_filter = "all crime types"
            print("Invalid selection. Using all crime types.")
    
    # Perform analysis based on choice
    if choice == '1':  # Weather conditions
        env_counts = filtered_df.groupby('Weather').size().reset_index(name='Crime_Count')
        env_counts = env_counts.sort_values('Crime_Count', ascending=False)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=env_counts, x='Weather', y='Crime_Count')
        plt.title(f'Crime Frequency by Weather Condition ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_weather.png')
        print("\nEnvironmental analysis chart saved to output/crime_by_weather.png")
        
        # Get summary
        max_weather = env_counts.iloc[0]
        print(f"\nWeather with highest crime rate: {max_weather['Weather']} with {max_weather['Crime_Count']} crimes")
        
        # Perform percentage analysis
        env_counts['Percentage'] = env_counts['Crime_Count'] / env_counts['Crime_Count'].sum() * 100
        print("\nCrime distribution by weather:")
        for _, row in env_counts.iterrows():
            print(f"{row['Weather']}: {row['Crime_Count']} crimes ({row['Percentage']:.2f}%)")
        
    elif choice == '2':  # Temperature ranges
        # Create temperature bins
        bins = [-5, 0, 10, 20, 30, 40, 50]
        labels = ['Very Cold (<0°C)', 'Cold (0-10°C)', 'Mild (10-20°C)', 
                  'Warm (20-30°C)', 'Hot (30-40°C)', 'Very Hot (>40°C)']
        filtered_df['Temp_Range'] = pd.cut(filtered_df['Temperature'], bins=bins, labels=labels, right=False)
        
        # Count crimes by temperature range
        env_counts = filtered_df.groupby('Temp_Range').size().reset_index(name='Crime_Count')
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=env_counts, x='Temp_Range', y='Crime_Count')
        plt.title(f'Crime Frequency by Temperature Range ({crime_filter})')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('output/crime_by_temperature.png')
        print("\nEnvironmental analysis chart saved to output/crime_by_temperature.png")
        
        # Get summary
        max_temp = env_counts.loc[env_counts['Crime_Count'].idxmax()]
        print(f"\nTemperature range with highest crime rate: {max_temp['Temp_Range']} with {max_temp['Crime_Count']} crimes")
        
    elif choice == '3':  # Lighting conditions
        env_counts = filtered_df.groupby('Lighting').size().reset_index(name='Crime_Count')
        env_counts = env_counts.sort_values('Crime_Count', ascending=False)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=env_counts, x='Lighting', y='Crime_Count')
        plt.title(f'Crime Frequency by Lighting Condition ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_lighting.png')
        print("\nEnvironmental analysis chart saved to output/crime_by_lighting.png")
        
        # Get summary
        max_lighting = env_counts.iloc[0]
        print(f"\nLighting with highest crime rate: {max_lighting['Lighting']} with {max_lighting['Crime_Count']} crimes")
        
        # Calculate percentages
        total = env_counts['Crime_Count'].sum()
        for _, row in env_counts.iterrows():
            percentage = (row['Crime_Count'] / total) * 100
            print(f"{row['Lighting']}: {row['Crime_Count']} crimes ({percentage:.2f}%)")
        
    elif choice == '4':  # Weather + Lighting
        # Create a crosstab of weather vs lighting
        cross_tab = pd.crosstab(filtered_df['Weather'], filtered_df['Lighting'])
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlGnBu')
        plt.title(f'Crime Frequency by Weather and Lighting Conditions ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_weather_lighting.png')
        print("\nEnvironmental analysis chart saved to output/crime_by_weather_lighting.png")
        
        # Get max combination
        max_val = cross_tab.max().max()
        max_loc = [(i, j) for i in cross_tab.index for j in cross_tab.columns if cross_tab.loc[i, j] == max_val]
        print(f"\nHighest crime frequency: {max_val} crimes in {max_loc[0][0]} weather with {max_loc[0][1]} conditions")
    
    # Generate contextual insights if LLM is available
    if gemini_model and filtered_df.shape[0] > 0:
        print("\nGenerating environmental insights...")
        
        # Create a targeted query based on the analysis type
        if choice == '1':  # Weather
            query = f"How does weather affect {crime_filter} patterns? Analyze the relationship between different weather conditions and crime rates."
        elif choice == '2':  # Temperature
            query = f"How does temperature affect {crime_filter} patterns? Analyze the relationship between different temperature ranges and crime rates."
        elif choice == '3':  # Lighting
            query = f"How does lighting affect {crime_filter} patterns? Compare crime rates in well-lit versus poorly-lit areas."
        elif choice == '4':  # Weather + Lighting
            query = f"How do weather and lighting conditions together affect {crime_filter} patterns? Identify the most dangerous combinations."
        
        # Select relevant data for the LLM
        if choice in ['1', '2', '3']:
            if choice == '1':  # Weather
                # Get a sample of crimes from each weather condition
                relevant_records = pd.DataFrame()
                for weather in filtered_df['Weather'].unique():
                    weather_sample = filtered_df[filtered_df['Weather'] == weather].sample(
                        min(3, filtered_df[filtered_df['Weather'] == weather].shape[0])
                    )
                    relevant_records = pd.concat([relevant_records, weather_sample])
            elif choice == '2':  # Temperature
                # Get crimes from different temperature ranges
                relevant_records = pd.DataFrame()
                for temp_range in filtered_df['Temp_Range'].unique():
                    if pd.notna(temp_range):  # Handle potential NaN values
                        temp_sample = filtered_df[filtered_df['Temp_Range'] == temp_range].sample(
                            min(3, filtered_df[filtered_df['Temp_Range'] == temp_range].shape[0])
                        )
                        relevant_records = pd.concat([relevant_records, temp_sample])
            else:  # Lighting
                # Get crimes from each lighting condition
                relevant_records = pd.DataFrame()
                for lighting in filtered_df['Lighting'].unique():
                    light_sample = filtered_df[filtered_df['Lighting'] == lighting].sample(
                        min(5, filtered_df[filtered_df['Lighting'] == lighting].shape[0])
                    )
                    relevant_records = pd.concat([relevant_records, light_sample])
        else:
            # For combinations, get samples of the most common combinations
            relevant_records = filtered_df.sample(min(10, filtered_df.shape[0]))
        
        response = generate_contextual_response(query, relevant_records, model=gemini_model)
        print("\n--- Environmental Factor Analysis ---")
        print(response)
        print("---" * 10)
        
    input("\nPress Enter to continue...")

def socioeconomic_analysis(df, collections, gemini_model=None):
    """
    Analyze socioeconomic factors' impact on crime patterns
    """
    print("\n" + "="*30)
    print("SOCIOECONOMIC FACTOR ANALYSIS")
    print("="*30)
    
    print("\nSelect socioeconomic factor to analyze:")
    print("1. Population Density")
    print("2. Average Income")
    print("3. Unemployment Rate")
    print("4. Neighborhood Comparison")
    print("5. Correlation Analysis")
    
    choice = input("\nEnter choice (1-5): ")
    
    # Allow crime type filter
    print("\nFilter by crime type?")
    print("1. All crime types")
    crime_types = sorted(df['Crime_Type'].unique())
    for i, crime in enumerate(crime_types):
        print(f"{i+2}. {crime}")
    
    crime_choice = input("\nEnter choice: ")
    if crime_choice == '1':
        filtered_df = df.copy()
        crime_filter = "all crime types"
    else:
        try:
            crime_idx = int(crime_choice) - 2
            if 0 <= crime_idx < len(crime_types):
                crime_type = crime_types[crime_idx]
                filtered_df = df[df['Crime_Type'] == crime_type].copy()
                crime_filter = crime_type
            else:
                filtered_df = df.copy()
                crime_filter = "all crime types"
                print("Invalid selection. Using all crime types.")
        except Exception as e:
            filtered_df = df.copy()
            crime_filter = "all crime types"
            print("Invalid selection. Using all crime types.")
    
    # Perform analysis based on choice
    if choice == '1':  # Population Density
        # Create population density bins
        bins = [0, 2000, 5000, 8000, 12000, 15000]
        labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
        filtered_df['Pop_Density_Range'] = pd.cut(filtered_df['Population_Density'], bins=bins, labels=labels)
        
        # Count crimes by population density range
        socio_counts = filtered_df.groupby('Pop_Density_Range').size().reset_index(name='Crime_Count')
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=socio_counts, x='Pop_Density_Range', y='Crime_Count')
        plt.title(f'Crime Frequency by Population Density ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_population.png')
        print("\nSocioeconomic analysis chart saved to output/crime_by_population.png")
        
        # Get summary
        max_pop = socio_counts.loc[socio_counts['Crime_Count'].idxmax()]
        print(f"\nPopulation density range with highest crime rate: {max_pop['Pop_Density_Range']} with {max_pop['Crime_Count']} crimes")
        
    elif choice == '2':  # Average Income
        # Create income bins
        bins = [0, 100000, 200000, 300000, 400000, 600000]
        labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
        filtered_df['Income_Range'] = pd.cut(filtered_df['Average_Income'], bins=bins, labels=labels)
        
        # Count crimes by income range
        socio_counts = filtered_df.groupby('Income_Range').size().reset_index(name='Crime_Count')
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=socio_counts, x='Income_Range', y='Crime_Count')
        plt.title(f'Crime Frequency by Average Income ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_income.png')
        print("\nSocioeconomic analysis chart saved to output/crime_by_income.png")
        
        # Get summary
        max_income = socio_counts.loc[socio_counts['Crime_Count'].idxmax()]
        print(f"\nIncome range with highest crime rate: {max_income['Income_Range']} with {max_income['Crime_Count']} crimes")
        
    elif choice == '3':  # Unemployment Rate
        # Create unemployment rate bins
        bins = [0, 5, 8, 10, 12, 15, 20]
        labels = ['Very Low', 'Low', 'Medium-Low', 'Medium', 'Medium-High', 'High']
        filtered_df['Unemployment_Range'] = pd.cut(filtered_df['Unemployment_Rate'], bins=bins, labels=labels)
        
        # Count crimes by unemployment range
        socio_counts = filtered_df.groupby('Unemployment_Range').size().reset_index(name='Crime_Count')
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=socio_counts, x='Unemployment_Range', y='Crime_Count')
        plt.title(f'Crime Frequency by Unemployment Rate ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/crime_by_unemployment.png')
        print("\nSocioeconomic analysis chart saved to output/crime_by_unemployment.png")
        
        # Get summary
        max_unemp = socio_counts.loc[socio_counts['Crime_Count'].idxmax()]
        print(f"\nUnemployment range with highest crime rate: {max_unemp['Unemployment_Range']} with {max_unemp['Crime_Count']} crimes")
        
    elif choice == '4':  # Neighborhood Comparison
        # Aggregate socioeconomic factors by neighborhood
        neighborhood_stats = filtered_df.groupby('Neighborhood').agg({
            'Population_Density': 'mean',
            'Average_Income': 'mean',
            'Unemployment_Rate': 'mean',
            'Crime_Count': 'sum'
        }).reset_index()
        
        plt.figure(figsize=(12, 8))
        sns.scatterplot(data=neighborhood_stats, x='Average_Income', y='Crime_Count', size='Population_Density', 
                        hue='Unemployment_Rate', sizes=(20, 200), alpha=0.7)
        plt.title(f'Neighborhood Socioeconomic Comparison ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/neighborhood_comparison.png')
        print("\nSocioeconomic analysis chart saved to output/neighborhood_comparison.png")
        
        # Get summary
        max_crime_neighborhood = neighborhood_stats.loc[neighborhood_stats['Crime_Count'].idxmax()]
        print(f"\nNeighborhood with highest crime rate: {max_crime_neighborhood['Neighborhood']} with {max_crime_neighborhood['Crime_Count']} crimes")
        
    elif choice == '5':  # Correlation Analysis
        # Calculate correlation matrix
        correlation_matrix = filtered_df[['Population_Density', 'Average_Income', 'Unemployment_Rate', 'Crime_Count']].corr()
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title(f'Correlation Analysis ({crime_filter})')
        plt.tight_layout()
        plt.savefig('output/correlation_analysis.png')
        print("\nSocioeconomic analysis chart saved to output/correlation_analysis.png")
        
        # Get summary
        print("\nCorrelation matrix:")
        print(correlation_matrix)
    
    # Generate contextual insights if LLM is available
    if gemini_model and filtered_df.shape[0] > 0:
        print("\nGenerating socioeconomic insights...")
        
        # Create a targeted query based on the analysis type
        if choice == '1':  # Population Density
            query = f"How does population density affect {crime_filter} patterns? Analyze the relationship between different population density ranges and crime rates."
        elif choice == '2':  # Average Income
            query = f"How does average income affect {crime_filter} patterns? Analyze the relationship between different income ranges and crime rates."
        elif choice == '3':  # Unemployment Rate
            query = f"How does unemployment rate affect {crime_filter} patterns? Analyze the relationship between different unemployment rate ranges and crime rates."
        elif choice == '4':  # Neighborhood Comparison
            query = f"Compare the socioeconomic factors and crime rates across different neighborhoods for {crime_filter}."
        elif choice == '5':  # Correlation Analysis
            query = f"Analyze the correlation between socioeconomic factors and {crime_filter} rates. Identify the most significant correlations."
        
        # Select relevant data for the LLM
        if choice in ['1', '2', '3']:
            if choice == '1':  # Population Density
                # Get a sample of crimes from each population density range
                relevant_records = pd.DataFrame()
                for pop_range in filtered_df['Pop_Density_Range'].unique():
                    pop_sample = filtered_df[filtered_df['Pop_Density_Range'] == pop_range].sample(
                        min(3, filtered_df[filtered_df['Pop_Density_Range'] == pop_range].shape[0])
                    )
                    relevant_records = pd.concat([relevant_records, pop_sample])
            elif choice == '2':  # Average Income
                # Get crimes from different income ranges
                relevant_records = pd.DataFrame()
                for income_range in filtered_df['Income_Range'].unique():
                    income_sample = filtered_df[filtered_df['Income_Range'] == income_range].sample(
                        min(3, filtered_df[filtered_df['Income_Range'] == income_range].shape[0])
                    )
                    relevant_records = pd.concat([relevant_records, income_sample])
            else:  # Unemployment Rate
                # Get crimes from each unemployment rate range
                relevant_records = pd.DataFrame()
                for unemp_range in filtered_df['Unemployment_Range'].unique():
                    unemp_sample = filtered_df[filtered_df['Unemployment_Range'] == unemp_range].sample(
                        min(3, filtered_df[filtered_df['Unemployment_Range'] == unemp_range].shape[0])
                    )
                    relevant_records = pd.concat([relevant_records, unemp_sample])
        else:
            # For neighborhood comparison and correlation analysis, get a sample of the data
            relevant_records = filtered_df.sample(min(10, filtered_df.shape[0]))
        
        response = generate_contextual_response(query, relevant_records, model=gemini_model)
        print("\n--- Socioeconomic Factor Analysis ---")
        print(response)
        print("---" * 10)
        
    input("\nPress Enter to continue...")

def multi_factor_query(df, collections, gemini_model=None):
    """
    Perform multi-factor crime analysis
    """
    print("\n" + "="*30)
    print("MULTI-FACTOR CRIME QUERY")
    print("="*30)
    
    print("\nSelect factors to analyze:")
    print("1. Crime Hotspots + Temporal Patterns")
    print("2. Environmental + Socioeconomic Factors")
    print("3. All Factors Combined")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == '1':
        # Combine crime hotspots and temporal patterns
        print("\nCombining Crime Hotspots and Temporal Patterns...")
        crime_hotspot_analysis(df, collections, gemini_model)
        temporal_pattern_analysis(df, collections, gemini_model)
    elif choice == '2':
        # Combine environmental and socioeconomic factors
        print("\nCombining Environmental and Socioeconomic Factors...")
        environmental_factor_analysis(df, collections, gemini_model)
        socioeconomic_analysis(df, collections, gemini_model)
    elif choice == '3':
        # Combine all factors
        print("\nCombining All Factors...")
        crime_hotspot_analysis(df, collections, gemini_model)
        temporal_pattern_analysis(df, collections, gemini_model)
        environmental_factor_analysis(df, collections, gemini_model)
        socioeconomic_analysis(df, collections, gemini_model)
    else:
        print("\nInvalid choice. Please try again.")
    
    input("\nPress Enter to continue...")