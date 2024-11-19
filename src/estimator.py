import re
import statistics
from typing import List, Tuple


class Estimator:
    cps_values = []  # Characters per second values


    @staticmethod
    def clean_up(text: str) -> str:
        # Removes tags like <tag_name> from the text and returns the cleaned text
        text = re.sub(r'<[a-z_]+>', '', text)
        return text.strip()


    @staticmethod
    def estimate_tag_locations(text: str) -> List[Tuple[str, float]]:
        """
        Identifies tags in the text and calculates the estimated duration up to each tag's position.
        
        Returns:
            List of tuples containing (tag_content, estimated_duration).
        """
        tag_durations = []
        offset = 0
        cleaned_text = ""  # Accumulates the cleaned text
        current_position = 0  # Tracks the position in the original text

        while True:
            match = re.search(r'<[a-z_]+>', text)
            if not match:
                cleaned_text += text
                break  # No more tags found

            start, end = match.span()  # Start and end positions of the tag in the current text
            tag_content = match.group()[1:-1]  # Extract the tag content without '<' and '>'

            text_before_tag = text[:start]
            cleaned_text += text_before_tag

            characters_up_to_tag = len(cleaned_text)
            estimated_duration = Estimator.estimate_duration(characters_up_to_tag)
            print(estimated_duration)
            tag_durations.append((tag_content, estimated_duration))

            print(f"Found tag '{tag_content}' at position {current_position + start}, estimated duration: {estimated_duration:.2f} seconds")

            current_position += end

            # Remove the tag from the text
            text = text[end:]

        return tag_durations
        


    @staticmethod
    def statistic(characters: int, duration: float):
        """
        Collects data points and updates the median or mean characters per second.
        """
        if duration > 0:
            cps = characters / duration  # Calculate characters per second
            Estimator.cps_values.append(cps)
        else:
            print("Warning: Duration must be greater than zero. Data point ignored.")


    @staticmethod
    def estimate_duration(characters: int) -> float:
        if not Estimator.cps_values:
            print("No data available to estimate duration.")
            return 0.0

        estimated_cps = statistics.mean(Estimator.cps_values)

        # Estimate the duration
        estimated_duration = characters / estimated_cps
        return estimated_duration