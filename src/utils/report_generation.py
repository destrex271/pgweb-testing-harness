def write_to_report(listed_content: dict, title: str):
    with open("link_functionality_report.txt", "w+") as file:
        file.write("------------------------------------------------------------\n\n\t\t")
        file.write(f"{title}\n\n")
        file.write("------------------------------------------------------------\n\n")

        counter = 1

        for item in listed_content.keys():
            file.write(f"\t{counter}. {item} : {listed_content[item]}\n")
            counter += 1
        file.close()
