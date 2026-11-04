code = '''def measures_of_central_tendency_with_outliers(data: list, outliers: list) -> list:
    """
    Calculate Mean, Median, and Mode for original data and data with outliers.
    Compare results to understand the effect of outliers.

    Parameters:
        data: Original list of numerical values
        outliers: List of outlier values to add to the data

    Returns:
        list: [original_mean, original_median, original_mode,
               new_mean, new_median, new_mode]
              Each value as a float rounded to 4 decimal places.
    """
    
    # Helper functions for the formulas to avoid repetitive code
    def get_mean(lst):
        return sum(lst) / len(lst)

    def get_median(lst):
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_lst[mid - 1] + sorted_lst[mid]) / 2.0
        else:
            return float(sorted_lst[mid])

    def get_mode(lst):
        counts = {}
        for num in lst:
            counts[num] = counts.get(num, 0) + 1
        
        max_freq = max(counts.values())
        # Find all numbers that share the highest frequency
        modes = [num for num, freq in counts.items() if freq == max_freq]
        # Return the smallest if there is a tie
        return float(min(modes))

    # 1. Calculate original metrics (before adding outliers)
    orig_mean = round(get_mean(data), 4)
    orig_median = round(get_median(data), 4)
    orig_mode = round(get_mode(data), 4)

    # 2. Create the new dataset
    new_data = data + outliers

    # 3. Calculate new metrics
    new_mean = round(get_mean(new_data), 4)
    new_median = round(get_median(new_data), 4)
    new_mode = round(get_mode(new_data), 4)

    return [orig_mean, orig_median, orig_mode, new_mean, new_median, new_mode]'''

lines = code.splitlines()
print(f"Total lines: {len(lines)}")

predicted_monaco_indent = 0
for idx, line in enumerate(lines):
    raw = line.replace('\t', '    ')
    content = raw.lstrip(' ')
    target_indent = len(raw) - len(content)
    
    if not content:
        action = "ENTER (blank line)"
    elif idx == 0:
        action = f"Type line (indent {target_indent})"
        predicted_monaco_indent = target_indent + (4 if content.rstrip().endswith(':') else 0)
    else:
        diff = target_indent - predicted_monaco_indent
        if diff == 0:
            action = f"MATCH (0 spaces) -> type content"
        elif diff > 0:
            action = f"Type +{diff} spaces -> type content"
        else:
            action = f"Send {abs(diff)//4} Backspace(s) -> type content"
            
        ends_colon = content.rstrip().endswith(':')
        predicted_monaco_indent = target_indent + (4 if ends_colon else 0)
        
    print(f"L{idx+1:2d} (T={target_indent:2d}, M={predicted_monaco_indent:2d}): {action:38s} | {content[:35]}")
