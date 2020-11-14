#!/usr/bin/env python
# coding: utf-8

# # Naturela data extraction

# In[3]:


import pandas as pd
import matplotlib.pyplot   as plt
import seaborn             as sns; sns.set()
import plotly.express      as px


# ## Defining connection to the database

# In[1]:


from sqlalchemy import create_engine
postgres_str = ('postgresql://natu_user:password*01@pg-database-1.cwzau02gc3hn.us-east-2.rds.amazonaws.com:5432/naturela_dev')
# Create the connection
cnx = create_engine(postgres_str)


# ## Reading the sales from the source

# Sales data is read from the 'raw/ventas.csv', with semicolon separator, and must have the next names and order:
# * vtanum, vtafec, tercod, ternom, procod, pronom, terrzn, cant, pround, precio, kilos, propeso, subtot, prfcod, prfnom, vlrkilo, pronomdet, zoncod, zonnom, vencod, vennom, ciucod, costo, terdir, provcod, provnom, ciunom, venced.
# 
# The way used to put the file in the folder is not treat in current process

# In[6]:


ventas = pd.read_csv('raw/ventas.csv', sep=';',
                     dtype = {"venced": "str"})#, nrows=1000)
ventas.drop(columns=['zoncod', 'zonnom', 'provcod', 'provnom'], inplace=True)


# ## Transforming data

# Discard sales with unuseless products

# In[7]:


print("Total rows before:",ventas['vencod'].count())
drop_products = ['ALIM NAT. GREEN FIBER PL X 200 GR','PASAB. ROSQUI SPIRUNAT TRADI 40GR PLX18'
                 ,'PASAB. ROSQUI SPIRUNAT TRADI 75GR PLX12','PASAB. ROSQUI SPIRUNAT VEGA 40GR PLX18'
                 ,'ALIM NAT. GREEN FIBER SPIRUNAT PL 200GR','ALIM NAT. 100%SPIRULINA SPIRUNAT PVO 100GR'
                 ,'ALIM NAT. 100% CURCUMA SPIRUNAT PVO 60GR','ALIM NAT. SPIRACTIVE SPIRUNAT PVO 510GR'
                 ,'4PACK ROSQUILLAS TRADI','4PACK ROSQUILLAS VEGA','PALITOS PAN DE ARROZ Y LINAZA'
                 ,'FLETE  NO GRAVADO','FLETE VINCULADAS','FLETES 16%','EJEMPLO']
ventas = ventas[~ventas.pronom.isin(drop_products)]
print("Total rows after:",ventas['vencod'].count())


# ## Reading clients from the source

# Clients data is read from the 'raw/clientes_naturela.csv', with semicolon separator, and must have the next names and order:
# * Nombre Cliente (Factura), Nombre del Establecimiento (Aviso), Tipo de Identificación, Número de Identificación, Tipo de Persona, Tipo de Cliente, Naturaleza Económica, Condición Adicional, País, Ciudad, Dirección Sede Principal, Termino de Pago, ¿Tiene Crédito?, Cantidad de Establecimientos, Celular, Correo Electrónico, Persona de Contacto, Teléfono, Vendedor, Verificado, Zona.
# 
# The way used to put the file in the folder is not treat in current process

# In[8]:


clientes = pd.read_csv('raw/clientes_naturela.csv', sep=';')


# Deleting unuseless columns and renaming other ones

# In[9]:


clientes.drop(columns=['Teléfono','Celular','Cantidad de Establecimientos','Nombre del Establecimiento (Aviso)'], inplace=True)
clientes['Número de Identificación']= clientes['Número de Identificación'].str.split(" ", n = 1, expand = True) 
ventas['tercod'] = ventas['tercod'].astype(str)
clientes['Número de Identificación'].astype(str)
ventas_cli = pd.merge(ventas, clientes, how="left", left_on="tercod", right_on="Número de Identificación")
ventas_cli.rename(columns={'Nombre Cliente (Factura)':'client_name','Tipo de Identificación':'type_id'
                           ,'Número de Identificación':'cli_customer_ID','Tipo de Persona':'type_person'
                           ,'Tipo de Cliente':'type_client','Naturaleza Económica':'nature_economy'
                           ,'Condición Adicional':'aditional_condition','País':'country'
                           ,'Ciudad':'city','Dirección Sede Principal':'main_address'
                           ,'Termino de Pago':'payment_terms','¿Tiene Crédito?':'credit_state'
                           ,'Correo Electrónico':'email','Persona de Contacto':'contact_person'
                           ,'Vendedor':'seller','Verificado':'verified','Zona':'zone'}, inplace=True)


# In[10]:


print("Total sales:",ventas_cli["vencod"].count())
print("Total sales without client:",ventas_cli["cli_customer_ID"].isnull().sum())


# ## Merging sales data with clients

# In[11]:


clientes["Nombre Cliente (Factura)"] = clientes["Nombre Cliente (Factura)"].str.upper()
clientes["aux"] = None
ventas_cli = pd.merge(ventas_cli, clientes, how='left', left_on=['terrzn','cli_customer_ID'], right_on=['Nombre Cliente (Factura)','aux'])
for i in ventas_cli[(~ventas_cli["Nombre Cliente (Factura)"].isnull())].index:
    ventas_cli['client_name'][i] = ventas_cli["Nombre Cliente (Factura)"][i]
    ventas_cli['type_id'][i] = ventas_cli['Tipo de Identificación']
    ventas_cli['tercod'][i] = ventas_cli['Número de Identificación']
    ventas_cli['type_person'][i] = ventas_cli['Tipo de Persona']
    ventas_cli['type_client'][i] = ventas_cli['Tipo de Cliente']
    ventas_cli['nature_economy'][i] = ventas_cli['Naturaleza Económica']
    ventas_cli['aditional_condition'][i] = ventas_cli['Condición Adicional']
    ventas_cli['country'][i] = ventas_cli['País']
    ventas_cli['city'][i] = ventas_cli['Ciudad']
    ventas_cli['main_address'][i] = ventas_cli['Dirección Sede Principal']
    ventas_cli['payment_terms'][i] = ventas_cli['Termino de Pago']
    ventas_cli['credit_state'][i] = ventas_cli['¿Tiene Crédito?']
    ventas_cli['email'][i] = ventas_cli['Correo Electrónico']
    ventas_cli['contact_person'][i] = ventas_cli['Persona de Contacto']
    ventas_cli['seller'][i] = ventas_cli['Vendedor']
    ventas_cli['verified'][i] = ventas_cli['Verificado']
    ventas_cli['zone'][i] = ventas_cli['Zona']


# Dropping unuseless columns from the resultant dataframe:

# In[12]:


ventas_cli.drop(columns=['Nombre Cliente (Factura)','Tipo de Identificación','cli_customer_ID'
                         ,'Número de Identificación','Tipo de Persona'
                         ,'Tipo de Cliente','Naturaleza Económica'
                         ,'Condición Adicional','País','Ciudad'
                         ,'Dirección Sede Principal','Termino de Pago'
                         ,'¿Tiene Crédito?','Correo Electrónico'
                         ,'Persona de Contacto','Vendedor','Verificado'
                         ,'Zona','aux','propeso','pronomdet','prfcod','prfnom'], inplace=True)


# Transforming date:

# In[13]:


ventas_cli['vtafec']= ventas_cli['vtafec'].str.split(" ", n = 1, expand = True) 


# Renaming columns and dropping blank spaces:

# In[14]:


ventas_cli.rename(columns={'vtanum':'invoice_number','vtafec':'invoice_date'
                            ,'tercod':'customer_id','ternom':'contact_name'
                            ,'procod':'product_code','pronom':'product_name'
                            ,'terrzn':'customer_name','cant':'quantity'
                            ,'pround':'sales_unit','precio':'sales_unit_price'
                            ,'kilos':'kilos','propeso':'deleted'
                            ,'subtot':'price_bef_vat','prfcod':'deleted'
                            ,'prfnom':'deleted','vlrkilo':'price_per_kilo'
                            ,'pronomdet':'deleted','vencod':'salesperson_code'
                            ,'vennom':'salesperson_name','ciucod':'city_code'
                            ,'costo':'cost','terdir':'invoice_address'
                            ,'ciunom':'city_name','venced':'salesperson_id'}, inplace=True)


# In[15]:


ventas_cli['sales_unit_price'] = ventas_cli['sales_unit_price'].str.replace(',', '.')
ventas_cli['price_bef_vat'] = ventas_cli['price_bef_vat'].str.replace(',', '.')
ventas_cli['price_per_kilo'] = ventas_cli['price_per_kilo'].str.replace(',', '.')
ventas_cli['cost'] = ventas_cli['cost'].str.replace(',', '.')


# In[16]:


ventas_cli["product_code"] = ventas_cli["product_code"].str.replace(';','')
ventas_cli["product_name"] = ventas_cli["product_name"].str.replace(';','')
ventas_cli["customer_name"] = ventas_cli["customer_name"].str.replace(';','')
ventas_cli["sales_unit"] = ventas_cli["sales_unit"].str.replace(';','')
ventas_cli["salesperson_name"] = ventas_cli["salesperson_name"].str.replace(';','')
ventas_cli["invoice_address"] = ventas_cli["invoice_address"].str.replace(';','')
ventas_cli["city_name"] = ventas_cli["city_name"].str.replace(';','')
ventas_cli["client_name"] = ventas_cli["client_name"].str.replace(';','')
ventas_cli['type_id'] = ventas_cli['type_id'].replace(';','')
ventas_cli['type_id'] = ventas_cli['type_id'].str.strip()
ventas_cli["type_person"] = ventas_cli["type_person"].replace(';','')
ventas_cli["type_person"] = ventas_cli["type_person"].str.strip()
ventas_cli["type_client"] = ventas_cli["type_client"].replace(';','')
ventas_cli["type_client"] = ventas_cli["type_client"].str.strip()
ventas_cli["nature_economy"] = ventas_cli["nature_economy"].str.strip().replace(';','')
ventas_cli["aditional_condition"] = ventas_cli["aditional_condition"].str.strip().replace(';','')
ventas_cli["country"] = ventas_cli["country"].str.strip().replace(';','')
ventas_cli["city"] = ventas_cli["city"].str.strip().replace(';','')
ventas_cli["main_address"] = ventas_cli["main_address"].str.strip().replace(';','')
ventas_cli["payment_terms"] = ventas_cli["payment_terms"].str.strip().replace(';','')
ventas_cli["credit_state"] = ventas_cli["credit_state"].str.strip().replace(';','')
ventas_cli["email"] = ventas_cli["email"].str.strip().replace(';','')
ventas_cli["contact_person"] = ventas_cli["contact_person"].str.strip().replace(';','')
ventas_cli["seller"] = ventas_cli["seller"].str.strip().replace(';','')
ventas_cli["verified"] = ventas_cli["verified"].str.strip().replace(';','')
ventas_cli["zone"] = ventas_cli["zone"].str.strip().replace(';','')
ventas_cli["customer_id"].fillna('0', inplace=True)
ventas_cli["customer_id"] = ventas_cli["customer_id"].str.strip()
ventas_cli.to_csv(r'process/ventas.csv',sep=';',index=False)


# Cleaning errors in column invoice_number:

# In[17]:


ventas_cli.drop(ventas_cli[ventas_cli['invoice_number']=="vtanum"].index, inplace = True)


# ## Adding data to table sales_01 in the database

# In[19]:


try:
    trun = pd.read_sql_query('''truncate table public.sales_01''', cnx)
except:
    print("Table sales_01 doesn't exist")
ventas_cli.to_sql('sales_01', cnx, index=False, if_exists='append')


# ## Fixing wrong products codes in the table sales_01

# Some sales come from the transactional systems with different codes but correspond to the same product. 

# In[ ]:


line = pd.read_sql_query('''
update sales_01 set product_code = '65024', product_name = 'PASAB. ROSQUI NATURELA TRADI 40 GR BSX6' where product_code = '65031';
update sales_01 set product_code = 'PT05', product_name = 'INFU. TE SPIRUTE VERDE PL X 30 UN 45GR' where product_code = 'PT162';
update sales_01 set product_code = '65026', product_name = 'PASAB. ROSQUI NATURELA VEGA 40 GR BSX6' where product_code = '65030';
update sales_01 set product_code = 'PT136', product_name = 'ALIM NAT. 100% CURCUMA NATURELA 60GR' where product_code = 'PT167';
update sales_01 set product_code = 'PT155', product_name = 'INFU. TE SPIRUTE CURCUMA PL X 30 UN 45GR' where product_code = 'PT164';
update sales_01 set product_code = 'PT117', product_name = 'INFU. TE SPIRUTE MORINGA PL X 30 UN 45GR' where product_code = 'PT163';
update sales_01 set product_code = 'PT174', product_name = 'ALIM. NAT SPIRACTIVE PROTEINA X 210G' where product_code = '1046593';
update sales_01 set product_code = 'PT01', product_name = 'ALIM NAT. 100% SPIRULINA NATURELA 100GR' where product_code = 'PT161';
update sales_01 set product_code = 'PT08', product_name = 'ALIM NAT. GREEN 3 BEBIDA PL X 200 ML' where product_code = 'PT165';
update sales_01 set product_code = '65037', product_name = 'PASAB.ROSQUI NATURELA TRADI 210 GR' where product_code = '1043670';
update sales_01 set product_code = '65023', product_name = 'PAN ARROZ ROSQUILLA CHIA LINAZA 40G  *12' where product_code = '2010704';
update sales_01 set product_code = '65028', product_name = 'PASAB. ROSQUI NATURELA SURTIDAX40G.BSX6' where product_code = '1048828';
update sales_01 set product_code = '65025', product_name = 'PASAB. ROSQUI NATURELA VEGA 40 GR BSX12' where product_code = '2010706';
update sales_01 set product_code = 'PT05', product_name = 'TÉ VERDE SPIRULINA SPIRUTÉ 30 BOLS *45G' where product_code = 'PT05 A';
update sales_01 set product_code = '65024', product_name = 'PASAB. ROSQUI NATURELA TRADI 40 GR BSX6' where product_code = '1048815';
update sales_01 set product_code = 'PT155', product_name = 'INFU. TE SPIRUTE CURCUMA PL X 30 UN 45GR' where product_code = '1048818';
update sales_01 set product_code = '65027', product_name = 'PAN ARROZ ROSQUILLA SPIRULINA MACA 40G * 12' where product_code = '2010707';
update sales_01 set product_code = 'PT06', product_name = 'INFU. TE SPIRUTE ROJO PL X 30 UN 45GR' where product_code = '1045446';
update sales_01 set product_code = 'PT117', product_name = 'INFU. TE SPIRUTE MORINGA PL X 30 UN 45GR' where product_code = '1048819';
update sales_01 set product_code = 'PT175', product_name = 'INFU. TE SPIRUTE CACAO PL X 30 UN 45GR' where product_code = '1047878';
update sales_01 set product_code = 'PT05', product_name = 'INFU. TE SPIRUTE VERDE PL X 30 UN 45GR' where product_code = '1048817';
update sales_01 set product_code = 'PT155', product_name = 'TÉ DORADO CÚRCUMA SPIRUTÉ X 30 *45G' where product_code = 'PT155A';
update sales_01 set product_code = '65026', product_name = 'PASAB. ROSQUI NATURELA VEGA 40 GR BSX6' where product_code = '1048816';
update sales_01 set product_code = 'PT03', product_name = 'ALIM NAT. 100% SPIRULINA NATURELA 100GR' where product_code = '1048821';
update sales_01 set product_code = 'PT136', product_name = 'ALIM NAT. 100% CURCUMA NATURELA 60GR' where product_code = '1048822';
update sales_01 set product_code = 'PT117', product_name = 'TÉ MORINGA NATURAL SPIRUTÉ X30 *45G' where product_code = 'PT117 A';
update sales_01 set product_code = 'PT05', product_name = 'INFU. TE SPIRUTE VERDE PL X 30 UN 45GR' where product_code = '2010697';
update sales_01 set product_code = 'PT06', product_name = 'INFU. TE SPIRUTE ROJO PL X 30 UN 45GR' where product_code = '2010698';
update sales_01 set product_code = 'PT155', product_name = 'INFU. TE SPIRUTE CURCUMA PL X 30 UN 45GR' where product_code = '2010700';
update sales_01 set product_code = 'PT06', product_name = 'TÉ ROOIBOS NATURAL SPIRUTÉ X30BOL *45G' where product_code = 'PT06 A';
update sales_01 set product_code = 'PT147', product_name = 'ALIM POLVO MIX SPIRULINA+MACA*100G' where product_code = 'PT147 A';
update sales_01 set product_code = 'PT117', product_name = 'TÉ MORINGA NATURAL SPIRUTÉ 30 BOLS  *45G' where product_code = '1047300';
update sales_01 set product_code = 'PT117', product_name = 'INFU. TE SPIRUTE MORINGA PL X 30 UN 45GR' where product_code = '2010699';
update sales_01 set product_code = 'PT03', product_name = 'ALIM NAT. 100% SPIRULINA NATURELA 100GR' where product_code = '2010701';
update sales_01 set product_code = 'PT122', product_name = 'ALIM HOJUELAS SPIRULINA 100% *12G' where product_code = '2010702';
update sales_01 set product_code = 'PT03', product_name = 'ALIM POLVO SPIRULINA 100% PURA *100G' where product_code = 'PT03 A';
update sales_01 set product_code = 'PT136', product_name = 'ALIMENTO POLVO CÚRCUMA 100% PURA *60G' where product_code = 'PT136A';
update sales_01 set product_code = 'PT173', product_name = 'SPIRULINA PROTEIN BALLS *6' where product_code = 'PT173 A';
update sales_01 set product_code = 'PT06', product_name = 'TÉ ROOIBOS NATURAL SPIRUTÉ X30BOL *45G' where product_code = 'PT06A';
update sales_01 set product_code = 'PT175', product_name = 'TÉ CACAO  NATURAL SPIRUTÉ 30 BOLS *45G' where product_code = 'PT175A';
update sales_01 set product_code = 'PT145', product_name = 'MENTAS SIN AZÚCAR SPIRUMENTA *18G' where product_code = 'PT145 A';
update sales_01 set product_code = 'PT153', product_name = 'ALIM POLVO MIX SPIRULINA+ ACAI*100G' where product_code = 'PT153 A';
update sales_01 set product_code = 'PT59', product_name = 'ALIM POLVO PROTEÍNA SPIRACTIVE*510G' where product_code = 'PT59 A';
update sales_01 set product_code = 'PT08' where product_code = '65022';
''', cnx)

