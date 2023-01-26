def get_pipeline(form, query_dict):
    pipeline = []
    # Check for text input
    for field_name, value in list(form.data.items())[:-2]:
        if value != "":
            regex_pattern = f".*{value}.*"
            regex_params = {
                "path": field_name,
                "query": regex_pattern,
                "allowAnalyzedField": True
            }
            regex_dict = {}
            regex_dict["regex"] = regex_params
            query_dict["$search"]["compound"]["filter"].append(regex_dict)

    pipeline.append(query_dict) if len(query_dict["$search"]["compound"]["filter"]) != 0 else 0  # Append nothing

    # Check for sort
    order = form.order_by.data
    if order:
        sort = {
            "$sort": {
                order: -1
            }
        }
        pipeline.append(sort)

    return pipeline

