import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
from wordcloud import WordCloud
import re

# Set up the Streamlit page
st.set_page_config(layout="wide", page_title="Karir.com Data Dashboard")
st.title("📊 Karir.com Data Dashboard")

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv('lowongan_karir_cleaned_with_salary_range.csv')
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    df = df.dropna(subset=['Tanggal'])
    df['Bulan'] = df['Tanggal'].dt.to_period('M')

    df['Gaji Minimum'] = pd.to_numeric(df['Gaji Minimum'], errors='coerce')
    df['Gaji Maksimum'] = pd.to_numeric(df['Gaji Maksimum'], errors='coerce')
    df['Gaji Rata-Rata'] = (df['Gaji Minimum'] + df['Gaji Maksimum']) / 2

    return df

df = load_data()

# Sidebar filter
st.sidebar.header("🔍 Filter Data")

# Filter Gaji
min_salary = st.sidebar.slider('Minimum Salary (IDR)', 0, 25000000, 0, 500000)
max_salary = st.sidebar.slider('Maximum Salary (IDR)', 0, 25000000, 25000000, 500000)

# Filter Lokasi
selected_locations = st.sidebar.multiselect(
    "Select Location(s)", options=df['Lokasi'].dropna().unique(), default=list(df['Lokasi'].dropna().unique())
)

# Filter Pengalaman Minimal
experience_options = df['Pengalaman Minimal'].dropna().unique()
selected_experience = st.sidebar.multiselect(
    "Select Experience Level(s)", options=experience_options, default=list(experience_options)
)

# Filter Jenjang Karir
career_levels = df['Jenjang Karir'].dropna().unique()
selected_career = st.sidebar.multiselect(
    "Select Career Level(s)", options=career_levels, default=list(career_levels)
)

# Filtering data
filtered_df = df[
    (df['Gaji Rata-Rata'] >= min_salary) &
    (df['Gaji Rata-Rata'] <= max_salary) &
    (df['Lokasi'].isin(selected_locations)) &
    (df['Pengalaman Minimal'].isin(selected_experience)) &
    (df['Jenjang Karir'].isin(selected_career))
]

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Time Trends", "🏢 Company & Location", "💰 Salary", "☁️ Keywords", "📈 Career Level"
])

# Tab 1 - Time Trends
with tab1:
    st.subheader("Job Count per Day")
    if not filtered_df.empty:
        job_per_day = filtered_df.groupby('Tanggal').size().reset_index(name='Job Count')
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(job_per_day['Tanggal'], job_per_day['Job Count'], marker='o', color='b', linestyle='-')
        ax.set_title("Job Count per Day")
        ax.set_xlabel("Date")
        ax.set_ylabel("Job Count")
        plt.xticks(rotation=45)
        plt.grid(True)
        st.pyplot(fig)
    else:
        st.info("No data available for selected filters.")

# Tab 2 - Company & Location
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Companies")
        if not filtered_df.empty:
            top_companies = filtered_df['Perusahaan'].value_counts().head(10)
        else:
            top_companies = df['Perusahaan'].value_counts().head(10)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(top_companies.index, top_companies.values, color='orange')
        ax.set_title("Top 10 Companies")
        ax.set_xlabel("Company")
        ax.set_ylabel("Job Count")
        ax.set_xticks(range(len(top_companies.index)))
        ax.set_xticklabels(top_companies.index, rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("Top 10 Locations")
        if not filtered_df.empty:
            top_locations = filtered_df['Lokasi'].value_counts().head(10)
        else:
            top_locations = df['Lokasi'].value_counts().head(10)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(top_locations.index, top_locations.values, color='green')
        ax.set_title("Top 10 Locations")
        ax.set_xlabel("Location")
        ax.set_ylabel("Job Count")
        ax.set_xticks(range(len(top_locations.index)))
        ax.set_xticklabels(top_locations.index, rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

# Tab 3 - Salary
with tab3:
    st.subheader("Minimum Salary Distribution")
    salary_min = filtered_df[filtered_df['Gaji Minimum'] > 0]
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.histplot(salary_min['Gaji Minimum'], bins=50, color='orange', edgecolor='black')
    ax.axvline(salary_min['Gaji Minimum'].mean(), color='red', linestyle='--', label=f"Rata-rata: Rp {salary_min['Gaji Minimum'].mean():,.0f}")
    ax.set_title('Minimum Salary Distribution')
    ax.set_xlabel('Minimum Salary (IDR)')
    ax.set_ylabel('Job Count')
    ax.legend()
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'Rp {x:,.0f}'))
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("Maximum Salary Distribution")
    salary_max = filtered_df[filtered_df['Gaji Maksimum'] > 0]
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.histplot(salary_max['Gaji Maksimum'], bins=50, color='blue', edgecolor='black')
    ax.axvline(salary_max['Gaji Maksimum'].mean(), color='red', linestyle='--', label=f"Rata-rata: Rp {salary_max['Gaji Maksimum'].mean():,.0f}")
    ax.set_title('Maximum Salary Distribution')
    ax.set_xlabel('Maximum Salary (IDR)')
    ax.set_ylabel('Job Count')
    ax.legend()
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'Rp {x:,.0f}'))
    plt.tight_layout()
    st.pyplot(fig)

# Tab 4 - Wordcloud
with tab4:
    st.subheader("Word Cloud of Job Descriptions")

    def clean_description(text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        return text

    text = ' '.join(filtered_df['Deskripsi Pekerjaan'].dropna().apply(clean_description).tolist())
    if text:
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        fig, ax = plt.subplots(figsize=(15, 7))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.info("No job description data available.")

# Tab 5 - Career Level
with tab5:
    st.subheader("Distribution of Career Levels")
    career_counts = filtered_df['Jenjang Karir'].value_counts()
    if not career_counts.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.pie(career_counts.values, labels=career_counts.index, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        plt.title("Career Level Distribution")
        st.pyplot(fig)
    else:
        st.info("No career level data available.")
