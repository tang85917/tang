feet_inches = input('Enter feet and inches: ')


def parse(feet_inches):
    parse = feet_inches.split(' ')
    feet = float(parse[0])
    inches = float(parse[1])
    return feet, inches


def convert(feet, inches):
    meters = feet * 0.3048 + inches * 0.0254
    return meters


f, i = parse(feet_inches)
print('fi', f, i)

result = convert(f, i)

if result < 1:
    print('Kid is too small.')
else:
    print('Kid can use the slide.')