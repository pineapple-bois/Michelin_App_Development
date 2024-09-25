from fuzzywuzzy import fuzz, process
from unidecode import unidecode


class LocationMatcher:
    def __init__(self, df, threshold=80):
        self.df = df.copy()  # Copy of the dataframe to avoid altering the original
        self.threshold = threshold  # Threshold for fuzzy matching

        # Normalize the 'location' column and split it into city and postal code
        self.df['normalized_city'] = self.df['location'].apply(lambda loc: self.normalize_text(self.split_location_field(loc)[0]))

        # Normalize the 'capital' column for capital city comparison
        self.df['normalized_capital'] = self.df['capital'].apply(self.normalize_text)

    @staticmethod
    def normalize_text(text):
        # Convert text to lowercase, remove accents using unidecode, and strip extra spaces
        if isinstance(text, str):
            return unidecode(text).lower().strip()
        return ""

    @staticmethod
    def split_location_field(location):
        # Split the location into city and postal code if available
        city, postal_code = None, None
        if location:
            parts = location.split(', ')
            city = parts[0]  # First part is the city
            if len(parts) > 1:
                postal_code = parts[1]  # Second part is the postal code (if available)
        return city, postal_code

    def get_region_department(self, city):
        normalized_city = self.normalize_text(city)
        city_matches = process.extractOne(normalized_city, self.df['normalized_city'], scorer=fuzz.token_sort_ratio)

        # Ensure the match score is above the threshold
        if city_matches and city_matches[1] >= self.threshold:
            matched_city = city_matches[0]
            # print(f"\nBest match found: {matched_city} with score {city_matches[1]}")

            # Extract the row for the matched city
            matched_row = self.df[self.df['normalized_city'] == matched_city].iloc[0]

            # Check if the city matches the department's capital
            is_capital = matched_row['normalized_capital'] == matched_city
            capital_status = "Department Capital" if is_capital else ""

            return {
                'matched_city': matched_row['location'],  # Original location field (city and postal code)
                'region': matched_row['region'],
                'department': matched_row['department'],
                'capital_status': capital_status  # Return "Department Capital" if applicable
            }
        else:
            return None

    def find_region_department(self, city_input):
        # First, extract city and postal code
        city, postal_code = self.split_location_field(city_input)
        if city:
            # Fuzzy match the city and get the region and department
            result = self.get_region_department(city)
            if result:
                return {
                    'Matched Location': result['matched_city'],
                    'Region': result['region'],
                    'Department': result['department'],
                    'Is Capital': result['capital_status']
                }
            else:
                return "No match found."
        else:
            return "Invalid input."