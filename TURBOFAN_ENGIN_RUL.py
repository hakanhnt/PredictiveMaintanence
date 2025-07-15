#!/usr/bin/env python
# coding: utf-8

# # Turbofan Engine Predictive Maintanence
# 

# # İçindekiler

# 1.   Veri setinin tanımı
# 2.   Verilerin yüklenmesi
#       *   pandas kütüphanesi ile verilerin dataframe'e yüklenmesi.
#       *   Dataframe'de yer alan özellik bilgilerinin gösterilmesi.
# 3.   Veri temizleme işlemleri
#       *   Boş hücrelerin temizlenmesi
#       *   Boş hücrelerin mean ile doldurulması
# 4.   İstatistiksel veri analizi
#       * Veri seti hakkında istatistiksel bilgiler
#       * Korelasyon Tablosu
# 5.   Veri görselleştirme
#       *   Line, scatter plot
#       *   sns, matplotlib
# 6.   Isolation Forest yöntemi ile kümelemeye bağlı outlier ve anomali tespiti.
#       *   Anomaly skoru
#       *   Normal, Anomali tespiti
# 7.   Özellik Çıkarımı ve Seçimi
#       *   Özellik önemi
#       *   Kısmi bağımlılıklar
# 8.   Sınıflandırma ve Regresyon Yöntemleriyle(ML) Tahminleme
#       *   Random Forest
#       *   GridSearch, KFold
# 
# 
# 

# **1. Veri Setinin Tanımı**
# 
# ```
# # Dataset: NASA Turbofan Engine Degradation Simulation Data Set (Remaining Useful Life Estimation) - C-MAPSS
# #Uçak motorunun kalan kararlı yaşam süresinin tahminlemesi.
# #Güncel sensör değerlerine göre kaç adım sonra motorun bakıma ihtiyaç duyacağını tahminliyoruz.
# #Kestirimci Bakım (Predictive Maintainence)
# #Sorun oluşmadan önce sorunun oluşacağının proses verileriyle tahmin edilmesi.
# #RUL nedir?
# `  Remaining Useful Life (yararlı ömür) bir komponent'in çalışmaya başladığı andan itibaren kalan kararlı yaşam süresidir.`
# *Kalan kullanım ömrü
# ```
# 
# 

# ![alt text](https://www.metabunk.org/sk/Turbofan3_exhaust-animated.gif)

# In[1]:


import numpy as np
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
#from sklearn.externals import joblib
from sklearn.preprocessing import StandardScaler


# **2. Verilerin Yüklenmesi**
# 
# CSV formatındaki verileri, ***`pandas`*** paketini kullanarak bir dataframe'e yüklüyoruz. Veri setindeki genel bilgileri(özelliklerin sayısı, tipi vs.) gösteriyoruz.
# 

# **pandas** => verilerin bütüncül bir şekilde çerçevelendirilmesini sağlar ve içerisinde matematiksel, istatistiksel fonksiyonları barındırır.

# In[ ]:


df=pd.read_csv("RUL_DATA.csv")


# In[ ]:


#dataframe(veri çerçevesi)
df


# In[ ]:


df.info()


# **3. Veri Temizleme İşlemleri**
# 1.   Veri setinde yer alan boş veya alakasız verileri siliyoruz.
# 2.   Eksik olan alanları forward fill(bir önceki değer) ile dolduruyoruz.

# In[ ]:


df.dropna(inplace=True)


# In[ ]:


df.fillna(method="ffill")


# **4. İstatistiksel Veri Analizi**
# 
# 
# 
# 
# 1.   Veri seti içeresinde yer alan her bir özelliğin sayısı, mean'i, max'ı, standart sapması gibi değerleri gösteriyoruz.
# 2.   Veri setindeki nümerik özelliklerin birbirleri arasındaki ilişkiye bakıyoruz.
# 
# 
# 

# In[ ]:


df.describe()


# Burada standart sapma değeri çok küçük(0'a yakın) olan özellikleri veri setimizden çıkarıyoruz. Çünkü modelleme yaparken bu özelliklerin hiçbir etkisi olmayacak. (*S18*, *S19*)

# In[ ]:


drop_features = ['S18', 'S19']
df.drop(drop_features, axis=1, inplace=True)


# Veri setinden atılan özelliklerden sonra veri setimizdeki özellikleri listeliyoruz.

# In[ ]:


df.columns


# In[ ]:


sensor_columns = ['S1', 'S2', 'S3', 'S4', 'S5',
       'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16',
       'S17', 'S20', 'S21']
op_columns = ['Op1', 'Op2', 'Op3']
target = 'RUL'


# Veri setimizde yer alan özelliklerin birbiriyle ve RUL ile olan pozitif ve negatif yöndeki ilişkisini korelasyon yöntemi ile hesaplıyoruz.

# In[ ]:


corr = df.drop(['Unit', 'Cycle'], axis=1).corr()


# In[ ]:


f,ax = plt.subplots(figsize=(20, 15))
sns.heatmap(corr, annot=True, linewidths=.5, fmt= '.1f',ax=ax)


# **5. Veri Görselleştirme**
# 
# 
# 1.   Her bir özelliğe ait dağılım grafiğini RUL'a bağlı çizdiriyoruz.
# 2.   Her bir özelliğe ait dağılım grafiğini OP1 ve OP2'ye göre çizdiriyoruz.
# 
# 

# In[ ]:


df[sensor_columns].plot()


# In[ ]:


df[target].plot()


# RUL'a bağlı özelliklerin dağılım grafiklerini görüyoruz.

# In[ ]:


explore = sns.PairGrid(
    data=df.query('Unit < 20'),
    x_vars=target,
    y_vars=sensor_columns + op_columns,
    hue="Unit",
    height=5,
    aspect=2.5,
)
explore = explore.map(plt.scatter, alpha=0.5)
explore = explore.set(xlim=(500,0))
explore = explore.add_legend()


# In[ ]:


drop_sensors = ["S1", "S5", "S6", "S10", "S16"]


# Yukarıdaki grafiği incelediğimizde **S1,S5,S6,S10,S16,OP3** özelliklerinin modelleme yapmak için birşey ifade etmediğini görüyoruz. O yüzden bu özellikleri de veri setimizden çıkartabiliriz.

# In[ ]:


df.drop(drop_sensors, axis=1, inplace=True)


# In[ ]:


df.drop(['Op3'], axis=1, inplace=True)


# In[ ]:


for d in drop_sensors:
  if d in sensor_columns:
    sensor_columns.remove(d)


# In[ ]:


print('eğitime sokacağımız özellikler', sensor_columns)


# **6. Isolation Forest Yöntemi ile Kümelemeye Bağlı Outlier ve Anomali Tespiti**
# 
# 1.   RUL değeri 10'dan küçük olanları anomali kabul edip büyük olanları da normal kabul ediyoruz.
# 2.   Isolation Forest yöntemi ile anomali ve normal kümelerimizi oluşturuyoruz.
# 
# 

# In[ ]:


from sklearn.ensemble import IsolationForest
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import GridSearchCV

RUL_THRESHOLD = 10

forest = IsolationForest()

X = df.drop(['RUL', 'Unit', 'Cycle'], axis=1)
y = df['RUL'] > RUL_THRESHOLD

skf = StratifiedKFold(n_splits=3)
folds = list(skf.split(X, y))
forest = IsolationForest()
ps = {"n_estimators": (55, 75, 95, 115), "contamination": np.linspace(0.03, 0.05, 15)}
search = GridSearchCV(estimator=forest, param_grid=ps, scoring='f1_micro', cv=folds)
search.fit(X, y)


# In[ ]:


df_search = pd.DataFrame(search.cv_results_)
df_search[["mean_test_score", "std_test_score", "params"]].sort_values(by=["mean_test_score"], ascending=False).head()


# In[ ]:


est = search.best_estimator_
est.fit(X, y)


# In[ ]:


preds = est.predict(X)


# In[ ]:


print('anomali sayısı', len(np.where(preds == -1)[0]))
print('normal sayısı', len(np.where(preds == 1)[0]))


# In[ ]:


anomaly_scores = est.score_samples(X.values)


# In[ ]:


X['scores'] = anomaly_scores
X['cluster_label'] = preds
X['RUL'] = df['RUL']


# In[ ]:


an_df = X[X['cluster_label'] == -1]


# **Anomali oluşturan değerlerin tablosu**

# In[ ]:


print(an_df.to_string())


# * En büyük anomali değerine sahip satırda RUL(model tarafından bilinmiyor) değerinin 0 olduğunu görüyoruz.

# In[ ]:


an_df.loc[830: 900]


# **Anomali tespitinde öne çıkan özellikleri, özellik önem sırasına göre çizdiriyoruz.**

# In[ ]:


preds


# In[ ]:


from sklearn import ensemble
an_model = ensemble.RandomForestClassifier()
an_model = ensemble.RandomForestClassifier(n_estimators=100, max_depth=15)
X = df[['S4', 'S11', 'S15']]
y = preds
an_model.fit(X, y)


# In[ ]:


import matplotlib.pyplot as plt

important_features = pd.Series(data=an_model.feature_importances_,index=X.columns)
important_features.sort_values(ascending=True,inplace=True)
important_features.plot(kind='barh')
# print(important_features.head(20))


# **7. Özellik Çıkarımı ve Seçimi**
# 
# 
# 1.   Sensör değerlerinin RUL'a göre RandomForest Regresyon yöntemi ile fit edilmesi.
# 2.   En yüksek öneme sahip özelliklerin çıkarılması.
# 
# 

# ![alt text](https://statistics.laerd.com/spss-tutorials/img/lr/linear-nonlinear-relationships.png)

# In[ ]:


drop_features_no_target = ['Unit', 'Cycle', 'Op1', 'Op2']
feature_selection_df = df.drop(drop_features_no_target, axis=1)
print(feature_selection_df.shape)


# In[ ]:


## X = df[['S9', 'S8', 'S3', 'S2', 'S7', 'S6', 'S4', 'S13', 'S12', 'S11', 'S17', 'S15', 'S14', 'S20', 'S21']]
X = df[['S9', 'S8', 'S3', 'S2', 'S7', 'S4', 'S13', 'S12', 'S11', 'S17', 'S15', 'S14', 'S20', 'S21']]

y = df['RUL']


# In[ ]:


from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X, y)


# In[ ]:


from sklearn import ensemble
model = ensemble.RandomForestRegressor()
model = ensemble.RandomForestRegressor(n_estimators = 200, max_depth = 15)
model.fit(X, y)
y_pred = model.predict(X)


# In[ ]:


from sklearn import ensemble
model = ensemble.ExtraTreesRegressor()
model = ensemble.ExtraTreesRegressor(n_estimators = 200, max_depth = 15)
model.fit(X, y)
y_pred = model.predict(X)


# In[ ]:


import matplotlib.pyplot as plt

important_features = pd.Series(data=model.feature_importances_,index=X.columns)
important_features.sort_values(ascending=True,inplace=True)
important_features.head(20).plot(kind='barh')
print(important_features.tail(10))


# **8.Sınıflandırma ve Regresyon Yöntemleriyle(ML) Tahminleme**
# 
# 
# 1.   ML Regresyon
# 2.   ML Sınıflandırma
# 
# 

# Nümerik ve kategorik özellikleri belirleyip train ve test setimizi
# 
# 1.   Train - %80
# 2.   Test - %20
# 
# olarak hazırlıyoruz.

# In[ ]:


categorical = df.select_dtypes(include=['object'])
numeric = df.select_dtypes(exclude=['object'])

y = numeric['RUL'] #hedef
X = numeric.drop(['RUL'], axis = 1) #sensör değerleri


# Train ve test olarak veri setimizi ikiye bölüyoruz. Veri setinin **%80'i train için %20'si** de test için ayrılıyor. Buradaki verilerin dağılımı train ve test kümesine rastgele yapılıyor.

# In[ ]:


import numpy as np
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1339) #train ve test kümelerine verilerin rastgele dağıtımı yapılıyor.


# 
# **Random Forest Regressor**

# **Grid Search** yöntemi ile modelimizin fit etmesini sağlayan en iyi parametreleri arıyoruz. En iyi parametrelere sahip modeli belirledikten sonra test verisi ile hata hesaplamalarını gerçekleştiriyoruz.

# In[ ]:


from sklearn.ensemble import RandomForestRegressor
from sklearn import preprocessing
rf = ensemble.RandomForestRegressor()
from sklearn import model_selection
cv = model_selection.KFold(5)
from sklearn.pipeline import Pipeline
pipeline = Pipeline(steps=[('standardize', preprocessing.StandardScaler())
                           , ('model', rf) ])
# Parameter grid trimmed for quicker execution
min_samples_leaf = [2, 10]
max_depth = [7, 8]
from sklearn.model_selection import GridSearchCV
optimized_rf = GridSearchCV(estimator=pipeline
                            , cv=cv
                            , param_grid =dict(model__min_samples_leaf = min_samples_leaf, model__max_depth = max_depth)
                            , scoring = 'neg_mean_squared_error'
                            , verbose = 1
                            , n_jobs = -1
                           )
optimized_rf.fit(X_train, y_train)
print(optimized_rf.best_estimator_)
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
y_pred = optimized_rf.predict(X_test)
print("Random Forest Mean Squared Error: ", mean_squared_error(y_test, y_pred))
print("Random Forest Mean Absolute Error: ", mean_absolute_error(y_test, y_pred))
print("Random Forest r-squared: ", r2_score(y_test, y_pred))


# Test verileriyle tahmin edilen veriler arasındaki farkı scatter plot ile çizdiriyoruz.

# In[ ]:


fig, ax = plt.subplots()
ax.scatter(y_test, y_pred, edgecolors=(0, 0, 0))
# ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=4)
ax.set_xlabel('Actual RUL')
ax.set_ylabel('Predicted RUL')
ax.set_title('RUL / Predicted')
plt.show()


# **Sınıflandırma(Random Forest)**

# ![alt text](https://thumbs.gfycat.com/RigidFantasticBlackfly-size_restricted.gif)

# Çözüme yönelik yaklaşımımızı **RUL = 0** anından geriye dönük **20 satırı, 1(Bakıma ihtiyaç duyduğu aralık)**, **20 satırdan büyük olanları, 0 (normal çalışma aralığı)** olacak şekilde değiştirip verimizi sınıflandırmaya uygun hale getiriyoruz.

# In[ ]:


cycles = 20
df['Target_20_Cycles'] = np.where(df['RUL'] <= cycles, 1, 0 )
df.tail(25)


# In[ ]:


from sklearn import preprocessing
categorical = df.select_dtypes(include=['object'])
numeric = df.select_dtypes(exclude=['object'])
# print(categorical.columns.values)
for name, values in categorical.items():
    dummies = pd.get_dummies(values.str.strip(), prefix = name, dummy_na=True)
    numeric = pd.concat([numeric, dummies], axis=1)
for name in numeric:
    if pd.isnull(numeric[name]).sum() > 0:
        numeric["%s_mi" % (name)] = pd.isnull(numeric[name])
        median = numeric[name].median()
        numeric[name] = numeric[name].apply(lambda x: median if pd.isnull(x) else x)
y = numeric['Target_20_Cycles']
X = numeric.drop(['Target_20_Cycles', 'RUL'], axis = 1)


# In[ ]:


import numpy as np
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1234)
from sklearn import ensemble
from sklearn.ensemble import RandomForestClassifier
# Limit number of trees for faster execution
rf = ensemble.RandomForestClassifier(n_estimators=100)

from sklearn import model_selection
cv = model_selection.KFold(5)

from sklearn.pipeline import Pipeline
pipeline = Pipeline(steps=[('standardize', preprocessing.StandardScaler())
                           , ('model', rf) ])
my_min_samples_leaf = [2, 25]
my_max_depth = [8, 9]

from sklearn.model_selection import GridSearchCV
optimized_rf = GridSearchCV(estimator=pipeline
                            , cv=cv
                            , param_grid =dict(model__min_samples_leaf = my_min_samples_leaf, model__max_depth = my_max_depth)
                            , scoring = 'roc_auc'
                            , verbose = 1
                            , n_jobs = -1
                           )
optimized_rf.fit(X_train, y_train)

y_pred_proba = optimized_rf.predict_proba(X_test)[:, 1]
y_pred = optimized_rf.predict(X_test)


# **Sınıflandırma Sonuçlarının Değerlendirilmesi**

# In[ ]:


from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, confusion_matrix
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))
from sklearn.metrics import classification_report
print("Random Forest Accuracy: "+"{:.1%}".format(accuracy_score(y_test, y_pred)));
print("Random Forest Precision: "+"{:.1%}".format(precision_score(y_test, y_pred)));
print("Random Forest Recall: "+"{:.1%}".format(recall_score(y_test, y_pred)));
print("Classification Report:")
print(classification_report(y_test, y_pred))
from sklearn import metrics
fpr, tpr, threshold = metrics.roc_curve(y_test, y_pred_proba)
roc_auc = metrics.auc(fpr, tpr)
import matplotlib.pyplot as plt
plt.title('ROC')
plt.plot(fpr, tpr, 'b', label = 'AUC = %0.2f' % roc_auc)
plt.legend(loc = 'lower right')
plt.plot([0, 1], [0, 1],'r--')
plt.xlim([0, 1])
plt.ylim([0, 1])
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')
plt.show()


# In[ ]:


conf_matrix = confusion_matrix(y_test,  y_pred)

plt.figure(figsize=(6, 6))
sns.heatmap(conf_matrix, xticklabels=['Normal', 'Anomali'], yticklabels=['Normal', 'Anomali'], annot=True, fmt="d")
plt.title("Confusion matrix")
plt.ylabel('Predicted class')
plt.xlabel('True class')
plt.show()


# 336 + 55  = *391* anomalinin 55'ini **normal** olarak yanlış geri kalanını **anomali** olarak doğru tahmin etmiş
# 
# 3677 + 59 = 3736 normal değerin 59'unu **anomali** olarak yanlış geri kalanını **normal** olarak doğru tahmin etmiş
# 
# 

# **Sınıflandırmaya bağlı özellik önemlerinin belirlenmesi**

# In[ ]:


rf_model = optimized_rf.best_estimator_.named_steps['model']
importances = rf_model.feature_importances_
importances = pd.Series(data=importances,index=X.columns)
importances.sort_values(ascending=True,inplace=True)
importances.head(20).plot(kind='barh')
print(importances.tail(10))


# Sınıflandırmayı etkileyen en önemli özellikler yukarıda görülmektedir. Regresyon yönteminden farklı olarak burada **S4** en önemli özellik olarak görünüyor.
