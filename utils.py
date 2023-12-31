from regex import R
from sklearn.pipeline import make_pipeline
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from collections import Counter
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OrdinalEncoder, RobustScaler
from imblearn.over_sampling import SMOTENC
import io
import pandas as pd
import fontawesome as fa
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import io
from imblearn.over_sampling import SMOTE, RandomOverSampler
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from collections import Counter
import fontawesome as fa
import sys
from sklearn.neighbors import LocalOutlierFactor
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_selection import SelectFromModel
from boruta import BorutaPy
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn import metrics
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import matthews_corrcoef
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.tree import DecisionTreeClassifier
import lightgbm as lgb
from sklearn import tree
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import AdaBoostClassifier
import xgboost as xgb
import sklearn_json as skljson
import shap
import sklearn
import matplotlib
import matplotlib.pyplot as pl
import matplotlib.pylab as plt
from imblearn.combine import SMOTETomek
from imblearn.under_sampling import TomekLinks
import warnings
warnings.filterwarnings('ignore')
from sklearn import datasets, ensemble, model_selection
from sklearn.datasets import make_multilabel_classification
from io import BytesIO
import sys
from sklearn.model_selection import RepeatedKFold
from mrmr import mrmr_classif

def has_nulls(df):
    nulls = df.isna().sum().sum()
    if nulls > 0:
        return True
    return False
    
def null_count(df):
    return df.isna().sum().sum()

def has_categ_columns(df):
    for col in df.columns:
        if df[col].dtype.name in ["category", "object"]:
            return True
    return False

def categ_columns(df):
    if(not has_categ_columns):
        return []
    categ_columns = []
    for col in df.columns:
        if df[col].dtype.name in ["category", "object"]:
            categ_columns.append(col)
    return categ_columns


def encode_categorical_columns(df):
    for col in df.columns:
        if df[col].dtype.name in ["category", "object"]:
            le = preprocessing.LabelEncoder()
            df[col] = le.fit_transform(df[col])
            #df[col] = df[col].astype("category")
            #df[col] = df[col].cat.codes
    return df

def numerical_columns(df):
    numerical_columns = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numerical_columns.append(col)
    return numerical_columns   

def check_for_outliers(df):

    outlier_count = 0
    numerical_columns_ = numerical_columns(df)
    for col in numerical_columns_:
        percentile25 = df[col].quantile(0.25)
        percentile75 = df[col].quantile(0.75)
        iqr = percentile75 - percentile75
        upper_limit = percentile75 + 1.5 * iqr
        lower_limit = percentile25 - 1.5 * iqr
        ul = np.where(df[col] > upper_limit, upper_limit, df[col])
        ll = np.where(df[col] < lower_limit, lower_limit, df[col])
        outlier_count += len(ul + ll)

    if outlier_count > 0:
        return True


def is_imbalance(y):
    value_c = list(y.value_counts())
    if value_c[0] >= (3*value_c[1]) or 3*value_c[0] <= value_c[1]:
        return True
    return False

def drop_outlier(df, field_name):
    distance = 1.5 * (np.percentile(df[field_name], 75) - np.percentile(df[field_name], 25))
    df.drop(df[df[field_name] > distance + np.percentile(df[field_name], 75)].index, inplace=True)
    df.drop(df[df[field_name] < np.percentile(df[field_name], 25) - distance].index, inplace=True)


def drop_outliers(df):
    numerical_columns_ = numerical_columns(df)
    for col in numerical_columns_:
        drop_outlier(df, col)
    return df.reset_index(drop=True)

def attr(X, y, a):
    if a=='Recursive Feature Elimination':
        model = LogisticRegression(solver='lbfgs')
        rfe = RFE(model)
        fit = rfe.fit(X, y)
        df=rfe.transform(X)
        new_columns = list(X.columns[rfe.support_])

    elif a=='Based on Extra Trees Classifier':
        clf = ExtraTreesClassifier(n_estimators=50)
        fit = clf.fit(X, y)
        clf.feature_importances_
        model = SelectFromModel(clf, prefit=True)
        feature_idx = model.get_support()
        new_columns = list(X.columns[feature_idx])

    elif a=='Based on Random Forest Classifier':
        sel = SelectFromModel(RandomForestClassifier(n_estimators = 100))
        sel.fit(X, y)
        sel.get_support()
        feature_idx = sel.get_support()
        new_columns = list(X.columns[feature_idx])
        df = sel.transform(X)

    elif a=='LASSO':
        sel = SelectFromModel(LogisticRegression(C=1, penalty='l1', solver='liblinear'))
        sel.fit(X, np.ravel(y,order='C'))
        feature_idx = sel.get_support()
        X=pd.DataFrame(X,  columns=X.columns)
        new_columns = list(X.columns[feature_idx])
        df = sel.transform(X)

    elif a=='mRMR (minimum Redundancy - Maximum Relevance)':
        new_columns = mrmr_classif(X=X, y=y, K=round(X.shape[1]/2))

    return new_columns

def simple_imputer(df):
    cols = list(df.columns.values)
    imp_mean = SimpleImputer(missing_values= np.nan, strategy='most_frequent')
    df = pd.DataFrame(imp_mean.fit_transform(df), columns=cols)
    return df

def transform(df, categ_columns, numerical_columns, transformation):
    categ = df[categ_columns]
    numerical = df[numerical_columns]

    transformations = {
        'Normalization': preprocessing.Normalizer(), 
        'Min-max Standardization': preprocessing.MinMaxScaler(), 
        'Standardization': preprocessing.StandardScaler(), 
        'Robust Standardization': preprocessing.RobustScaler(),
    }
    if transformation is not 'None':
        numerical_pipeline = make_pipeline(transformations[transformation])
        numerical = pd.DataFrame(numerical_pipeline.fit_transform(numerical), 
                                 columns=numerical_columns)

    df = pd.concat([categ, numerical], axis=1)

    return df


def transform_features(x, a):
    # data transformation function
    try:
        dff = encode_categorical_columns(x)
    except:
        dff =x

    if a==0:
        normalizer = preprocessing.Normalizer()
        list = []
        for i in dff.columns:
            threshold = 10
            if dff[i].nunique() < threshold:
                list.append(i)
        adf = dff.copy()
        normalizer = preprocessing.Normalizer().fit(adf)
        adf= normalizer.transform(adf)
        xcolumns = dff.columns.values
        adf = pd.DataFrame(adf)
        for i in range(len(xcolumns)):
            adf= adf.rename(columns={i:xcolumns[i]})
        for i in list:
            adf[i] = dff[i]
        dff = adf

    if a==1:
        std = MinMaxScaler()
        list = []
        for i in dff.columns:
            threshold = 10
            if dff[i].nunique() < threshold:
                list.append(i)



        adf = dff.copy()
        std = std.fit(adf)
        adf= std.transform(adf)
        xcolumns = dff.columns.values
        adf = pd.DataFrame(adf)
        for i in range(len(xcolumns)):
            adf= adf.rename(columns={i:xcolumns[i]})
        for i in list:
            adf[i] = dff[i]
        dff = adf

    if a==2:
        std = StandardScaler()
        list = []
        for i in dff.columns:
            threshold = 10
            if dff[i].nunique() < threshold:
                list.append(i)

        adf = dff.copy()
        std = std.fit(adf)
        adf= std.transform(adf)
        xcolumns = dff.columns.values
        adf = pd.DataFrame(adf)
        for i in range(len(xcolumns)):
            adf= adf.rename(columns={i:xcolumns[i]})
        for i in list:
            adf[i] = dff[i]
        dff = adf

    if a==3:
        std = RobustScaler()
        list = []
        for i in dff.columns:
            threshold = 10
            if dff[i].nunique() < threshold:
                list.append(i)

        adf = dff.copy()
        std = std.fit(adf)
        adf= std.transform(adf)
        xcolumns = dff.columns.values
        adf = pd.DataFrame(adf)
        for i in range(len(xcolumns)):
            adf= adf.rename(columns={i:xcolumns[i]})
        for i in list:
            adf[i] = dff[i]
        dff = adf


    return dff

#def missing_forest_impute(x):
#    imputer = MissForest()
#    x = imputer.fit_transform(x,cat_vars=None)
#    return x



def smote_function(X,y, smote):
    categorical_features = np.argwhere(np.array([len(set(X.iloc[:,x])) for x in range(X.shape[1])]) <= 9).flatten()
    ##normalde buradaki <=10 du, bu haliyle bazı sayısalları kategorik yapıyor veya cinsiyeti kategorik görmüyor vs, bağlanıp bakmamız gerek aslında

    if smote=='SMOTE':
        try:
            sm = SMOTE()
            X, y = sm.fit_resample(X, y)
        except:
            ros = RandomOverSampler()
            X, y = ros.fit_resample(X, y)
    elif smote=='SMOTETomek':
        try:
            sm = SMOTETomek()
            X, y = sm.fit_resample(X, y)
        except:
            ros = RandomOverSampler(sampling_strategy='not majority')
            X, y = ros.fit_resample(X, y)

    elif smote=='SMOTE-NC' and len(categorical_features) !=0:
        try:
            sm = SMOTENC(categorical_features=categorical_features, 
                        sampling_strategy='not majority')
            X, y = sm.fit_resample(X, y)
        except:
            ros = RandomOverSampler(sampling_strategy='not majority')
            X, y = ros.fit_resample(X, y)

    elif smote=='SMOTE-NC' and len(categorical_features) == 0:
        try:
            sm = SMOTE()
            X, y = sm.fit_resample(X, y)
        except:
            ros = RandomOverSampler()
            X, y = ros.fit_resample(X, y)


    return X,y