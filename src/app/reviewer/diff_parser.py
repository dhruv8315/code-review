import re

class DiffParser:
    def __init__(self):
        pass

    def diff_parser(self, diff_text: list):
        """
        Parses the diff text and extracts file changes, including line numbers, change types (added or removed), and content.
        """
        files=[]
        current_file=None
        new_line_number=0

        #Iterating through each item in the diff_text(list)
        for item in diff_text:
            #Iterating through each key-value pair in the item(dictionary)
            for key, value in item.items():

                if key == 'filename':
                    if current_file:
                        files.append(current_file)
                    current_file = {
                        "File": value,
                        "changes": []
                    }
                
                else:
                    if key == 'patch' and value.startswith("@@"):
                        match = re.search(r"\+(\d+)", value)

                        if match:
                            new_line_number = int(match.group(1))
                        
                        for t in value.splitlines():
                            if not t.endswith('@@'):
                                if t.startswith("+"):
                                    current_file["changes"].append({
                                        "line_number": new_line_number,
                                        "change_type": "added",
                                        "content": t[1:]
                                    })
                                    new_line_number += 1
                                
                                elif t.startswith("-"):
                                    current_file["changes"].append({
                                        "line_number": new_line_number,
                                        "change_type": "removed",
                                        "content": t[1:]
                                    })
                    else:
                        if isinstance(value, str) and not value.startswith("\\"):
                            new_line_number += 1

        if current_file:
            files.append(current_file)
        
        return files
    """
    def diff_parser(self, diff_text: str):
       
        files=[]
        current_file=None
        new_line_number=0

        for item in diff_text:
            for key, value in item.items():
                
                print(f"Key: {key}, Value: {value}")
                if key == 'patch' and value.startswith("@@"):
                    match = re.search(r"\+(\d+)", value)
                    print(f"Match: {match}")

                    if match:
                        new_line_number = int(match.group(1))
                        print(f"New Line Number: {new_line_number}")

                elif isinstance(value, str) and value.startswith("+") and not value.startswith("+++"):
                    current_file["changes"].append({
                        "line_number": new_line_number,
                        "change_type": "added",
                        "content": value[1:]
                    })

                    new_line_number += 1

                elif isinstance(value, str) and value.startswith("-") and not value.startswith("---"):
                    current_file["changes"].append({
                        "line_number": new_line_number,
                        "change_type": "removed",
                        "content": value[1:]
                    })
                    print                 

                else:
                    if isinstance(value, str) and not value.startswith("\\"):
                        new_line_number += 1
        if current_file:
            files.append(current_file)
        
        return files
"""


text = [{'filename': 'hi.py', 'status': 'modified', 'additions': 1, 'deletions': 0, 'changes': 1, 'patch': '@@ -1 +1,2 @@\n print("Hello world")\n+print("dhruv-patch-2 files are added!!!")'},
        {'filename': 'hit.py', 'status': 'modified', 'additions': 0, 'deletions': 1, 'changes': 1, 'patch': '@@ -1 +1,2 @@\n print("Hello world")\n-print("dhruv-patch-3 files are added!!!")\n+print("dhruv-patch-234 files are added!!!")'}]

parser = DiffParser()
parsed_diff = parser.diff_parser(text)
print(parsed_diff)