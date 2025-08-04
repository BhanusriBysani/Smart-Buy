import pandas as pd

df = pd.DataFrame(columns=["username", "password"])
df.to_excel("user_data/users.xlsx", index=False, engine='openpyxl')
print("users.xlsx created successfully!")
