import bcrypt, string

print(bcrypt.gensalt(5))
lol = {
    "PASS": 12345
}

print(string.ascii_letters)

print({"PASS": "12345"} | lol)