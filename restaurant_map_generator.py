import folium
from folium.plugins import HeatMap, MeasureControl, FloatImage
import pandas as pd
from selenium import webdriver
from PIL import Image
import io
import os

# Load data
df = pd.read_csv("restaurants_yaounde_verified.csv")

# Custom icon URLs (can also use local files)
ICONS = {
    "restaurant": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    "bar": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
    "cafe": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png"
}

# Create base map
m = folium.Map(location=[3.8480, 11.5021], zoom_start=14, 
              tiles="CartoDB positron", control_scale=True)

# 1. Custom Icons with Filtering
def get_icon(place_type):
    if "bar" in place_type.lower():
        return folium.CustomIcon(ICONS['bar'], icon_size=(25,41))
    elif "cafe" in place_type.lower():
        return folium.CustomIcon(ICONS['cafe'], icon_size=(25,41))
    else:
        return folium.CustomIcon(ICONS['restaurant'], icon_size=(25,41))

# 2. BDM-Friendly Features
measure = MeasureControl(position="bottomleft")
m.add_child(measure)

# Add scale bar
FloatImage("https://i.imgur.com/5GjZKUJ.png", bottom=5, left=5).add_to(m)

# 3. Enhanced Popups with Export Links
for idx, row in df.iterrows():
    popup_html = f"""
    <div style="width:300px">
        <h4 style="color:#d35400;margin-bottom:5px">{row['Name']}</h4>
        <div style="border-top:1px solid #eee;padding-top:5px">
            <b>📍 SR {row['SR']}:</b> {row['Address']}<br>
            <b>☎️:</b> {row['Phone'] or 'N/A'}<br>
            <b>⭐:</b> {row['Rating']} ({row['User Ratings Total']} reviews)<br>
            <b>🍽️:</b> {row['Category'].replace('- ',', ')}<br>
            <a href="{row['URL']}" target="_blank" style="color:#2980b9">View on Google Maps</a>
        </div>
    </div>
    """
    
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        icon=get_icon(row['Category'])
    ).add_to(m)

# 4. Heatmap
HeatMap(df[['Latitude', 'Longitude']].values.tolist(), radius=15).add_to(m)

# Save interactive HTML
m.save("yaounde_restaurants.html")

# 5. PDF Export Function
def export_pdf(html_file, pdf_file, filters=None):
    options = {
        'page-size': 'A3',
        'orientation': 'Landscape',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm'
    }
    
    # Apply filters if provided
    if filters:
        filtered_df = df.query(filters)
        print(f"Exporting {len(filtered_df)} filtered locations")
        
    # Convert to PDF
    driver = webdriver.Chrome()
    driver.get(f"file://{os.path.abspath(html_file)}")
    time.sleep(5)  # Allow map to load
    driver.save_screenshot("temp.png")
    driver.quit()
    
    # Convert screenshot to PDF
    img = Image.open("temp.png")
    img.save(pdf_file, "PDF", quality=100)
    os.remove("temp.png")

# Example usage:
export_pdf("yaounde_restaurants.html", "high_rated.pdf", "Rating > 4")
