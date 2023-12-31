from hmac import new
import matplotlib
from sklearn.model_selection import train_test_split
import streamlit as st
import pandas as pd
import numpy as np
import csv
import spss_converter
import tempfile
import os
import utils
import modelling
import shap
import streamlit.components.v1 as components
import lime
from val import calc_score

st.set_option('deprecation.showPyplotGlobalUse', False)

st.title('XAI Platform')

tab1, tab2, tab3, tab4, tab5 = st.tabs(["File Upload", "Data Preprocessing", "Modelling", "SHAP", "LIME"])

df = None
new_df = None
preprocessed_df = None
uploaded_file = None
model_count = 0
target = []

with tab1:
    uploaded_file = st.file_uploader('Choose a file', 
                                type=['xls', 'xlsx', 'sav', 'csv', 'txt'])
    
    if uploaded_file is None:
            st.write('Please upload a file first.')
    
    if uploaded_file is not None:
        file_name = uploaded_file.name

        extention = uploaded_file.name.split('.')[1]

        if extention in ['xls', 'xlsx']:
            df = pd.read_excel(uploaded_file)

        elif extention == 'sav':
            st.write('If you are having issues, you can convert SPSS files here: https://secure.ncounter.de/spssconverter')
            df, metadata = spss_converter.to_dataframe(uploaded_file.getvalue())

        elif extention == 'csv':
            st.write('If your file is not working correctly, specify the delimeter here:')
            seperator = st.text_input('Seperator', ',')
            df = pd.read_csv(uploaded_file, sep=seperator)

        elif extention == 'txt':
            st.write('If your file is not working correctly, specify the delimeter here:')
            seperator = st.text_input('Seperator', ',')
            df = pd.read_csv(uploaded_file, sep=seperator)

        st.subheader('Data preview')
        if df is not None:
            cols = df.columns.tolist()
            
            st.write('Select predictive attributes')
            pred = st.multiselect('Predictive attributes', cols, default=cols[:-1])

            cols = [x for x in cols if x not in pred]
            col1, col2 = st.columns(2)
            with col1:
                st.write('Select target/output attribute')
                target = st.selectbox('Target attribute', cols)
                
            with col2:
                st.write('Select the class of interest')
                i_c = st.selectbox('Class of interest', df[target].dropna().unique().tolist())

            for cls in df[target].unique().tolist():
                print(cls)

            new_df = df[pred + [target]]
            class_of_interest = i_c

            categ_columns = [x for x in utils.categ_columns(new_df) if x not in [target]]
            numerical_columns = [x for x in utils.numerical_columns(new_df) if x not in [target]]

            with st.expander('Data Information', expanded=True):
                st.dataframe(new_df)
                col1, col2 = st.columns(2)
                with col1:
                    st.write('**Number of Instances:**', new_df.shape[0])
                    st.write('**Number of Predictive Attributes:**', len(pred))
                    st.write('**Number of Target Attributes:**', len([target]))
                    
                with col2:
                    st.write('**Number of Attributes:**', new_df.shape[1])
                    st.write('**Number of Classes:**', len(new_df[target].dropna().unique().tolist()))
                    st.write('**Class of Interest:**', i_c)  

with tab2:
        if new_df is None:
            st.write('Please upload a file first.')
    

        if new_df is not None:       
            with st.expander('Missing Data Analysis Results', expanded=True):
                missing = utils.has_nulls(new_df)
                m_c = 'No missing values'
                if(missing):
                    st.write('Total Missing Values:', utils.null_count(new_df))
                    m_c = st.radio('Missing Value Imputation Method:', 
                    ['Remove rows with missing values',])
                    #'Most-frequent imputation'])
                else:
                    st.write('No missing values found.')
            
            with st.expander('Class Imbalance Analysis', expanded=True):
                onehot_list = utils.categ_columns(new_df)
                class_imbalance = 'None'
                is_imb = utils.is_imbalance(new_df[target])
                if is_imb and len(onehot_list) == 0:
                    class_imbalance = st.radio('There is a class imbalance problem in the dataset. Select one of the following methods to resolve the class imbalance problem.',
                    ['None','SMOTE','SMOTETomek'])
                elif is_imb and len(onehot_list) != 0:
                    class_imbalance = st.radio('There is a class imbalance problem in the dataset. Select one of the following methods to resolve the class imbalance problem.',
                    ['None','SMOTE-NC'])
                else:
                    st.write('There is no class imbalance problem in the dataset.')
                
            
            with st.expander('Outlier Value Analysis Result', expanded=True):
                if utils.check_for_outliers(new_df) == 0:
                    outliers = 'No outliers'
                    st.write('No outlier values were detected in the data set.')
                else:
                    st.write('Outlier values are detected in the data set. Total Outlier Values:', utils.check_for_outliers(df))
                    outliers = st.radio('Remove outliers?',['No', 'Yes'])
                
            
            with st.expander('Transformation Methods', expanded=True):
                transformations = st.radio('Please choose one of the following methods for data transformation.',
                ['None',
                'Normalization', 
                'Min-max Standardization', 
                'Standardization', 
                'Robust Standardization'])
                
            
            with st.expander('Attribute Selection Methods', expanded=True):
                attribute_selection = st.radio('Please choose one of the following methods for attribute selection.',
                ['None',
                'Recursive Feature Elimination', 
                'Based on Extra Trees Classifier',
                'Based on Random Forest Classifier', 
                'LASSO',
                'mRMR (minimum Redundancy - Maximum Relevance)'])
                

            with st.expander('Preprocessing Pipeline', expanded=True):
                
                new_df_ = new_df.copy()
                for cls in new_df_[target].unique().tolist():
                    print(cls)
                st.write('**Missing data:**', m_c)
                if m_c == 'Remove rows with missing values':
                    new_df = new_df_.copy()
                    new_df = new_df.dropna().reset_index(drop=True)
                #if m_c == 'Most-frequent imputation':
                #    new_df = new_df_.copy()
                #    new_df = utils.simple_imputer(new_df)

                encoded_df = utils.encode_categorical_columns(new_df)


                X, y = encoded_df.drop([target], axis=1), encoded_df[target]
                X_, y_ = X.copy(), y.copy()
                if class_imbalance != 'None':
                    st.write('**Class imbalance handling strategy:**', class_imbalance)
                    X, y = X_, y_
                    X, y = utils.smote_function(encoded_df.drop([target], axis=1), encoded_df[target], class_imbalance)

                balanced_df = pd.concat([X, y], axis=1)
                balanced_df_ = balanced_df.copy()
                
                st.write('**Remove outliers:**', outliers)
                if outliers == 'Yes':
                     balanced_df = balanced_df_
                     balanced_df = utils.drop_outliers(balanced_df)
                if outliers == 'No':
                    balanced_df = balanced_df_


                X, y = balanced_df.drop([target], axis=1), balanced_df[target]

                new_columns = X.columns
                st.write('**Attribute selection method:**', attribute_selection)
                if attribute_selection == 'None':
                    new_columns = cols
                
                st.write('**Data transformation:**', transformations)
                if transformations != 'None':
                    X = utils.transform(X, categ_columns, numerical_columns, transformations)

                transformed_df = pd.concat([X, y], axis=1)

                target_col = transformed_df[target]
                transformed_df_ = transformed_df.copy()
                if attribute_selection != 'None':
                    transformed_df = transformed_df_
                    new_columns = utils.attr(transformed_df.drop([target], axis=1), 
                                             transformed_df[target], 
                                             attribute_selection)
                    transformed_df = transformed_df[new_columns]
                    transformed_df = pd.concat([transformed_df, target_col], axis=1)

                col1, col2 = st.columns(2)
                with col1:
                    st.write('**Number of Instances:**', transformed_df.shape[0])
                    st.write('**Number of Predictive Attributes:**', len(pred))
                    st.write('**Number of Target Attributes:**', len([target]))
                    
                with col2:
                    st.write('**Number of Attributes:**', transformed_df.shape[1])
                    st.write('**Number of Classes:**', len(transformed_df[target].dropna().unique().tolist()))
                    st.write('**Class of Interest:**', i_c)
                st.write('**Important Attributes:**', ', '.join(new_columns))

                preprocessed_columns = transformed_df.columns
                X_preprocessed, y_preprocessed = transformed_df.drop([target], axis=1), transformed_df[target]
                preprocessed_df = pd.concat([X_preprocessed, y_preprocessed], axis=1)

                try:
                    st.dataframe(preprocessed_df)
                    csv = transformed_df.to_csv().encode('utf-8')
                    st.download_button(
                    label="Download Preprocessed Data",
                    data=csv,
                    file_name=f'{file_name.split(".")[0]}_preprocessed.csv',
                    mime='text/csv')
                except:
                    st.write("Make sure you've selected your entire pipeline.")

with tab3:
    if preprocessed_df is None:
        st.write('Please ensure you have preprocessed your data.')
    if preprocessed_df is not None:
        X, y = preprocessed_df.drop([target], axis=1), preprocessed_df[target]
        with st.expander('Modelling', expanded=True):
            models = st.multiselect('Select Model', ['AdaBoost', 'CatBoost', 'Decision Tree', 'Gaussian Naive Bayes', 'Gradient Boosting', 'LightGBM', 'Logistic Regression', 
                                                    'Multilayer Perceptron (MLP)', 'Random Forest', 'Support Vector Machine', 'XGBoost'])
        
            # hyperparameter = st.radio('Hyperparameter Optimization', ['Yes', 'No'])
            # if hyperparameter == 'Yes':
            #     k_fold_opt = st.slider('Select k-fold:', 2, 10, 2, 1)

        # with st.expander('Validation', expanded=True): 
        #     val = st.radio('Select Validation Method', ['None', 'Holdout', 'Repeated Holdout', 'Stratified K-fold Cross Validation', 'Leave One Out Cross Validation', 
        #                                                 'Repeated Cross Validation', 'Nested Cross Validation'])
            
            

        #     if val == "Holdout":
        #         train_size = st.slider('Select the training dataset percentage:', 50, 100, 50, 5)
        #         x_train, x_test, y_train, y_test = train_test_split(X, y, train_size=train_size/100, random_state=42)

        #     if val == "Repeated Holdout":
        #         split_size = st.slider('Select split size:', 50, 100, 50, 5)
        #         repeats = st.slider('Select the number of repeats:', 5, 50, 5, 1)

        #     if val == "Stratified K-fold Cross Validation":
        #         k_fold = st.slider('Select k-fold:', 2, 10, 2, 1)

        #     if val == "Leave One Out Cross Validation":
        #         pass

        #     if val == "Repeated Cross Validation":
        #         k_fold = st.slider('Select k-fold:', 5, 10, 5, 1)
        #         repeats = st.slider('Select the number of repeats:', 5, 10, 5, 1)

        #     if val == "Nested Cross Validation":
        #         inner_k = st.slider('Select inner k-fold:', 5, 10, 5, 1)
        #         outer_k = st.slider('Select outer k-fold:', 5, 10, 5, 1)

        
        # with st.expander('Modelling Options', expanded=True):  
        #     st.write('**Models:**', ', '.join(models))
        #     st.write('**Hyperparameter Optimization:**', hyperparameter)
        #     st.write('**Validation Method:**', val)
        #     st.dataframe(preprocessed_df)
        with st.spinner('Please while we create models.'):
            model_list = {}
            models_created = []
            for model in models:
                if model in ['AdaBoost', 'Decision Tree', 'Gaussian Naive Bayes', 'Gradient Boosting', 'Logistic Regression', 
                        'Multilayer Perceptron (MLP)', 'Random Forest', 'Support Vector Machine']:
                    try:
                        st.write(f"**{model} Results:**")
                        model_list[model] = modelling.get_model(model).fit(X, y)
                        models_created.append(model)
                        scores = calc_score(model_list[model], X, y)
                        labels = ["accuracy", "f1_weighted", "precision_weighted","recall_weighted","roc_auc_ovr", "false_positive_rate", "true_positive_rate", "negative_predictive_value"]
                        scores = dict(zip(labels, scores))
                        st.dataframe(pd.DataFrame.from_dict(scores, orient='index', columns=['Score']))
                        model_count += 1
                    except:
                        st.write(f'**{model}** is not supported for the data you uploaded.')
                    

            for model in models:
                if model in ['XGBoost', 'LightGBM', 'CatBoost']:
                    try:
                        st.write(f"**{model} Results:**")
                        model_list[model] = modelling.get_model(model).fit(X, y)
                        models_created.append(model)
                        scores = calc_score(model_list[model], X, y)
                        labels = ["accuracy", "f1_weighted", "precision_weighted","recall_weighted","roc_auc_ovr"]
                        scores = dict(zip(labels, scores))
                        st.dataframe(pd.DataFrame.from_dict(scores, orient='index', columns=['Score']))
                        model_count += 1
                    except:
                        st.write(f'**{model}** is not supported for the data you uploaded.')

        # if model_count != 0:
        #     st.write('**Models:**', ', '.join(models_created))
        #     for model in model_list.keys():
        #         with st.expander(f'{model} Results', expanded=True):
        #             scores = calc_score(model_list[model], X, y)
        #             labels = ["accuracy", "f1_weighted", "precision_weighted","recall_weighted","roc_auc_ovr"]
        #             scores = dict(zip(labels, scores))
        #             st.dataframe(pd.DataFrame.from_dict(scores, orient='index', columns=['Score']))





with tab4:
    if preprocessed_df is None:
            st.write('Please upload a file first.')
    with st.spinner('Please while we explain the predictions.'):
        if model_count != 0:
            for model in model_list.keys():
                if model in ['XGBoost', 'CatBoost', 'Decision Tree', 'Gradient Boosting', 'Random Forest']:
                    st.write(model)
                    shap_values = shap.TreeExplainer(model_list[model]).shap_values(X)
                    st.pyplot(shap.summary_plot(shap_values, X))

                else:
                    st.write(model)
                    shap_values = shap.KernelExplainer(model_list[model].predict_proba, X).shap_values(X)
                    st.pyplot(shap.summary_plot(shap_values, X))


with tab5:
    if preprocessed_df is None:
            st.write('Please upload a file first.')
    with st.spinner('Please while we explain the predictions.'):
        if model_count != 0:
            st.dataframe(X)
            for model in model_list.keys():
                explainer = lime.lime_tabular.LimeTabularExplainer(np.array(X), feature_names=list(X.columns), categorical_features=categ_columns)
                instances = X.shape[0]
                inc_int = None
                if st.button('Random Instace', key=f'new_instance_{model}'):
                    inc_int = np.random.randint(0, instances)
                
                record = st.number_input('Instance', min_value=0, max_value=instances-1, value=0, step=1, key=f'instance_{model}')
                if st.button('Explain', key=f'explain_{model}'):
                    inc_int = record
                
                st.write(model)
                if inc_int is not None:
                    ic, pc = st.columns(2)
                    with ic:
                        st.write('**Instance:**', X.iloc[inc_int])
                    with pc:
                        st.write('**Prediction:**', model_list[model].predict_proba(np.array(X.iloc[inc_int]).reshape(1, -1)))
                    exp = explainer.explain_instance(np.array(X.iloc[inc_int]), model_list[model].predict_proba, num_features=5)
                    st.pyplot(exp.as_pyplot_figure())
