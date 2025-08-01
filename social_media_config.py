# Facebook user and search query scraper configuration
FACEBOOK = {

    "users": [
        'abscbnNEWS', 'rapplerdotcom', 'gmanews',
        'manilabulletin', 'sunstarphilippines', 'PhilstarNews',
        'inquirerdotnet', 'pagasa.dost.gov.ph', 'davaocitydrmmc',
        'NDRRMC', 'UNTVNewsRescue', 'PIAgovernment', 'DavaoDRRMO',
        'sunstardavaonews','PHIVOLCS', 'mrpsd.com.ph'
    ],

    "search_queries": [
        'FloodAlert', 'BahaPH', 
        'StreetFloodAlert', 'tsunamialert',
        'LandslideAlert', 'LandslidePH', 
        'FireAlert', '#FireandRescuePH', 
        'EarthquakeAlert', 'EarthquakePH',
        'RescuePH'
    ],
}

# X user and search query scraper configuration
X = {
    "users": [
        "ABSCBNNews", "rapplerdotcom", "gmanews",
        "dost_pagasa", "inquirerdotnet", "phivolcs_dost",
        "NDRRMC_OpCen",
    ],

    "search_queries": [
        "flood philippines", "Flood in Davao",
        "landslide philippines", "Landslide in Davao",
        "earthquake philippines", "Earthquake in Davao",
        "typhoon philippines", "Typhoon in Davao",
        "fire philippines", "Fire in Davao",
        "volcano eruption philippines", "Volcano eruption Davao",
        "disaster news philippines", "Disaster news Davao"
    ],
}

# keywords for filtering disaster-related posts
KEYWORDS = [
    # Typhoon / Storm
    "typhoon", "storm", "storm surge",
    "tropical storm", "tropical depression",
    "bagyo", "unos", "thunderstorm",       
    "#typhoon", "#storm" 

    # Rain / Weather
    "weather", "rain", "raining", "rainfall", "downpour", "showers",
    "drizzle", "heavy rain", "monsoon",
    "LPA", "low pressure area",
    "malakas na ulan",
    
    # Flood (and related)
    "flood", "flooding", "flash flood", "river overflow",
    "baha", "lunop", "Street Flood",      
    "#flood", "#FloodAlert", "#BahaPH", "#StreetFloodAlert",

    # Landslide / Mudslide
    "landslide", "mudslide", "soil erosion", "slope failure",
    "pagguho ng lupa", "nangurog",  
    "#landslide", "#LandslideAlert", "#LandslidePH",

    # Earthquake
    "earthquake", "aftershock", "ground shaking", "seismic",
    "linog", "pagyanig",       
    "#EarthquakeAlert", "#EarthquakePH",

    # Tsunami
    "tsunami", "tidal wave", "sea surge", "coastal surge",
    "daluyong",                     
    "#tsunami",

    # Fire / Wildfire
    "fire", "blaze", "burning", "wildfire",
    "sunog", "nasunog","apoy",            
    "#FireAlert",

    # Volcano
    "volcano", "volcanic", "eruption", "ashfall", "lava",
    "bulkan", "pagputok ng bulkan",  
    "#volcano",

    # General disaster / emergency
    "disaster", "emergency", "rescue", "relief",
    "evacuation", "#evacuation",

    # Warnings & Alerts
    "warning", "alert", "advisory", "bulletin",
    "babala", "abiso",              
    "#warning", "#alert",

    # Tagalog / Cebuano extras
    "pag-uga", "pagbaha", "paglikas", "malakas na ulan",
    "mainit na bato", "kalamidad", "sakuna",
    "pahimangno", "pasidaan",

    # Bisaya / Cebuano extras
    "nahulog ang yuta", "nabahaan",
    "kusog nga ulan", "ting-ulan",
    "kasamok", "tabang"
]
