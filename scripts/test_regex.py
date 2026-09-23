import re

def test():
    text = "Ia Questão \n 2a Questão \n 3ª Questão \n 20a Questão \n Questão 5"
    pattern = re.compile(r'(?:^|\n)\s*([0-9lI]{1,2})\s*(?:ª|º|\"|\'|”|“|11|\-|\.|\)|a|\s)*Quest(?:ã|a|)(?:o|)\b', re.IGNORECASE)
    splits = pattern.split(text)
    
    nums = []
    for i in range(1, len(splits), 2):
        s = splits[i].upper().replace('I', '1').replace('L', '1')
        nums.append(int(s))
    print("Found numbers:", nums)

if __name__ == "__main__":
    test()
