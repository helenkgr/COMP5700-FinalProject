import yaml
import os
import sys

# load and validate YAML file; return contents as dictionary
def load_yaml_file(filepath: str) -> dict:
    if not filepath:
        raise ValueError("Filepath cannot be empty.")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if not filepath.lower().endswith(".yaml") and not filepath.lower().endswith(".yml"):
        raise ValueError(f"File must be a YAML file: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"YAML file does not contain a valid dictionary: {filepath}")

    return data


# extract name field from each element in KDE dictionary
def get_kde_names(kde_dict: dict) -> set:
    names = set()
    for key, value in kde_dict.items():
        if isinstance(value, dict) and "name" in value:
            names.add(value["name"])
    return names


# compare YAML files by KDE names only and write differences to text file
def compare_kde_names(yaml1_path: str, yaml2_path: str, output_dir: str = "outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)

    # load YAML files
    kde1 = load_yaml_file(yaml1_path)
    kde2 = load_yaml_file(yaml2_path)

    # get names
    names1 = get_kde_names(kde1)
    names2 = get_kde_names(kde2)

    # find names that differ
    only_in_1 = names1 - names2
    only_in_2 = names2 - names1

    # build output filename from input filenames
    base1 = os.path.splitext(os.path.basename(yaml1_path))[0]
    base2 = os.path.splitext(os.path.basename(yaml2_path))[0]
    out_path = os.path.join(output_dir, f"name_diff_{base1}_vs_{base2}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        if not only_in_1 and not only_in_2:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT NAMES\n")
        else:
            for name in only_in_1:
                f.write(f"{name} only in {os.path.basename(yaml1_path)}\n")
            for name in only_in_2:
                f.write(f"{name} only in {os.path.basename(yaml2_path)}\n")

    return out_path


# compare YAML files by KDE names and reqs; write differences to text file
def compare_kde_requirements(yaml1_path: str, yaml2_path: str, output_dir: str = "outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)

    # load YAML files
    kde1 = load_yaml_file(yaml1_path)
    kde2 = load_yaml_file(yaml2_path)

    # build a lookup of name to reqs for each file
    def build_lookup(kde_dict):
        lookup = {}
        for key, value in kde_dict.items():
            if isinstance(value, dict) and "name" in value:
                name = value["name"]
                reqs = value.get("requirements", [])
                lookup[name] = set(reqs) if reqs else set()
        return lookup

    lookup1 = build_lookup(kde1)
    lookup2 = build_lookup(kde2)

    all_names = set(lookup1.keys()) | set(lookup2.keys())

    base1 = os.path.splitext(os.path.basename(yaml1_path))[0]
    base2 = os.path.splitext(os.path.basename(yaml2_path))[0]
    out_path = os.path.join(output_dir, f"req_diff_{base1}_vs_{base2}.txt")

    differences = []

    for name in all_names:
        in_1 = name in lookup1
        in_2 = name in lookup2

        # KDE present in one file but absent in the other
        if in_1 and not in_2:
            differences.append(f"{name},ABSENT-IN-{base2},PRESENT-IN-{base1},NA")
        elif in_2 and not in_1:
            differences.append(f"{name},ABSENT-IN-{base1},PRESENT-IN-{base2},NA")
        else:
            # KDE present in both; check for requirement differences
            reqs1 = lookup1[name]
            reqs2 = lookup2[name]
            only_in_reqs1 = reqs1 - reqs2
            only_in_reqs2 = reqs2 - reqs1

            for req in only_in_reqs1:
                differences.append(f"{name},ABSENT-IN-{base2},PRESENT-IN-{base1},{req}")
            for req in only_in_reqs2:
                differences.append(f"{name},ABSENT-IN-{base1},PRESENT-IN-{base2},{req}")

    with open(out_path, "w", encoding="utf-8") as f:
        if not differences:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS\n")
        else:
            for line in differences:
                f.write(line + "\n")

    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python comparator.py <yaml1> <yaml2>")
        sys.exit(1)
    compare_kde_names(sys.argv[1], sys.argv[2])
    compare_kde_requirements(sys.argv[1], sys.argv[2])