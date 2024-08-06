from .constants import URL


def format_entry_urls(content):
    formatted_content = ""
    content = str(content).split("<a")
    for i in range(len(content)):
        if i != 0:
            formatted_content += '<a'
        else:
            formatted_content += content[i]
            continue
        formatted_content += content[i]
        showing_text = content[i].split(">")[1].split("<")[0]
        print(showing_text)
        new_text = ''
        if showing_text.__contains__(URL):
            print("contains")
            if showing_text.__contains__("/entry"):
                print("entry")
                new_text = ">(bkz: entry)<"
            elif showing_text.__contains__("/title"):
                print("title")
                new_text = ">(bkz: title)<"
        if new_text:
            formatted_content = formatted_content.replace(
                '>' + showing_text + '<', new_text)
    return formatted_content


def content_is_empty(content):
    content = content.replace('&nbsp;', '').replace(
                '<p>', '').replace('</p>', '')
    return content.replace(' ', '') == ''
