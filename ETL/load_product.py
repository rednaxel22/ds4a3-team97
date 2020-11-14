#!/usr/bin/env python
# coding: utf-8

# # Load table products

# Product table  contain all products that are used in analysis. The next coding  is used to add new rows to the table product.

# In[2]:


import pandas as pd
from sqlalchemy import create_engine


# ## Defining connection to the database

# In[3]:


postgres_str = ('postgresql://natu_user:password*01@pg-database-1.cwzau02gc3hn.us-east-2.rds.amazonaws.com:5432/naturela_dev')
# Create the connection
cnx = create_engine(postgres_str)


# Loading actuals products in the database

# In[4]:


df_actual = pd.read_sql_query('''Select code from public.product''', cnx)


# ## Reading the new products from the source

# Data of new products is read from the 'raw/product.csv', with semicolon separator, and must have the next names and order:
# * description, code, presentation, product_line.
# 
# The way used to put the file in the folder is not treat in current process

# In[21]:


try:
    products = pd.read_csv('raw/product.csv', sep=';',
                     dtype = {"description":"str","code":"str"
                              ,"presentation":"str","product_line":"str"})
except:
    print("Read error")


# ## Discarting products that already exists in the database

# Only new products are added to the table

# In[19]:


final_data = products[(~products["code"].isin(df_actual["code"]))]


# ## Updating table product

# In[20]:


try:
    final_data.to_sql('product', cnx, index=False, if_exists='append')
except:
    print("Update error")

