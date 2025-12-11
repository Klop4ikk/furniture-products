import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db as db
import base64

def get_base64_logo(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# ✅ Настройки страницы
st.set_page_config(
    page_title='Комфорт',
    page_icon='resources/logo.ico',
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Тёмная тема + фиксированный хедер
st.markdown("""
    <style>
    /* Общий фон */
    .main {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }

    /* Боковая панель */
    section[data-testid="stSidebar"] {
        background-color: #252526 !important;
        color: #E0E0E0 !important;
        border-right: 1px solid #3C3C3C;
    }

    /* Заголовки */
    h1, h2, h3, h4 {
        color: #8AB4F8 !important;
        font-weight: 600;
    }

    /* Кнопки */
    .stButton > button {
        background-color: #3A3D41 !important;
        color: #E0E0E0 !important;
        border-radius: 6px;
        border: 1px solid #5A5A5A;
        padding: 8px 16px;
    }

    .stButton > button:hover {
        background-color: #4C4F54 !important;
        border-color: #7A7A7A;
    }

    /* Таблицы */
    .stDataFrame {
        background-color: #1E1E1E !important;
    }

    /* Карточки */
    .metric-card {
        background-color: #2D2D30;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3C3C3C;
        margin-bottom: 15px;
    }

    .success-box {
        background-color: #1F3D2D;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
    }

    .info-box {
        background-color: #2D2D30;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #3C3C3C;
    }

    /* Поля ввода */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background-color: #2D2D30 !important;
        color: #E0E0E0 !important;
        border: 1px solid #3C3C3C !important;
    }

    /* Разделители */
    hr {
        border: 1px solid #3C3C3C !important;
    }

    /* ✅ Фиксированный хедер */
    .fixed-header {
        position: fixed;
        top: 55px;
        left: 0;
        width: 100%;
        z-index: 9999;
        background-color: #1E1E1E;
        padding: 10px 20px;
        border-bottom: 1px solid #3C3C3C;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
    }

    /* ✅ Отступ для основного контента */
    .block-container {
        padding-top: 130px !important;
    }
    </style>
""", unsafe_allow_html=True)




# ✅ Инициализация состояния
if 'edit_product_id' not in st.session_state:
    st.session_state.edit_product_id = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'products'
if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = None


def main_header():
    logo_base64 = get_base64_logo("resources/logo.png")

    st.markdown(f"""
        <div class="fixed-header" style="
            display:flex;
            align-items:center;
            justify-content:center;
            gap:15px;
        ">
            <img src="data:image/png;base64,{logo_base64}" style="width:55px;">
            <h2 style="margin:0; color:#8AB4F8; font-weight:600;">
                Компания «Комфорт»
            </h2>
        </div>
    """, unsafe_allow_html=True)




    # Отступ под фиксированный хедер
    st.markdown("<div style='height:70px;'></div>", unsafe_allow_html=True)





# ✅ Боковая панель
def sidebar_navigation():
    with st.sidebar:
        st.markdown("### 📋 Навигация")

        menu = {
            "Продукция": "products",
            "Цеха производства": "workshops",
            "Расчёт сырья": "calculation"
        }

        for label, key in menu.items():
            if st.button(label, use_container_width=True):
                st.session_state.current_page = key
                st.session_state.show_add_form = False
                st.rerun()

        st.markdown("---")
        st.markdown("### ➕ Добавление продукции")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Добавить", use_container_width=True):
                st.session_state.show_add_form = True
                st.session_state.edit_product_id = None
                st.session_state.current_page = 'products'
                st.rerun()

        st.markdown("---")


# ✅ Страница продукции
def display_products_page():
    st.header("📦 Продукция")

    if st.session_state.show_add_form:
        display_product_form()
        return

    with st.spinner("Загрузка данных..."):
        products_df = db.get_products_with_production_time()

    if products_df.empty:
        st.warning("В базе данных нет продукции. Добавьте первый продукт.")
        return

    st.metric("Всего продукции", len(products_df))
    st.markdown("---")

    # ✅ Фильтры (оставлены на месте)
    st.subheader("🔍 Поиск и фильтрация")
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        types = db.get_unique_product_types()
        filter_type = st.selectbox("Тип продукции", ["Все"] + types)

    with col2:
        search_query = st.text_input("Поиск по названию")

    with col3:
        time_filter = st.selectbox("Время пр-ва", ["Все", "С указанием", "Без указания"])

    filtered = products_df.copy()

    if filter_type != "Все":
        filtered = filtered[filtered["product_type"] == filter_type]

    if search_query:
        filtered = filtered[filtered["name"].str.contains(search_query, case=False)]

    if time_filter == "С указанием":
        filtered = filtered[filtered["production_time_h"] > 0]
    elif time_filter == "Без указания":
        filtered = filtered[filtered["production_time_h"] == 0]

    st.success(f"Найдено: {len(filtered)} товаров")

    st.dataframe(filtered, use_container_width=True, hide_index=True, height=400)

    st.markdown("---")
    st.subheader("⚙️ Управление продуктами")

    col1, col2 = st.columns(2)

    with col1:
        product_options = {row["name"]: row["id"] for _, row in filtered.iterrows()}
        selected = st.selectbox("Выберите продукт", ["Выберите..."] + list(product_options.keys()))

    with col2:
        if selected != "Выберите...":
            pid = product_options[selected]
            tab1, tab2, tab3 = st.tabs(["✏️ Редактировать", "🗑️ Удалить", "⏱️ Время пр-ва"])

            with tab1:
                if st.button("Открыть форму"):
                    st.session_state.edit_product_id = pid
                    st.session_state.show_add_form = True
                    st.rerun()

            with tab2:
                if st.button("Удалить", type="secondary"):
                    db.delete_product(pid)
                    st.success("Удалено!")
                    st.rerun()

            with tab3:
                manage_production_time(selected)


# ✅ Управление временем производства
def manage_production_time(product_name):
    st.markdown(f"### ⏱️ Время производства: {product_name}")

    times = db.get_production_times_for_product(product_name)

    if times:
        df = pd.DataFrame(times)
        st.dataframe(df[["workshop_name", "production_time"]], hide_index=True)

        for rec in times:
            if st.button(f"Удалить {rec['workshop_name']}", key=f"del_{rec['id']}"):
                db.delete_production_time(rec["id"])
                st.success("Удалено!")
                st.rerun()
    else:
        st.info("Нет данных о времени производства.")

    st.markdown("---")
    st.subheader("Добавить время")

    with st.form(f"add_time_{product_name}"):
        col1, col2 = st.columns(2)

        with col1:
            workshops = db.get_available_workshops()
            workshop = st.selectbox("Цех", workshops)

        with col2:
            time = st.number_input("Время (ч)", min_value=0.0, step=0.5)

        if st.form_submit_button("Добавить"):
            db.add_production_time(product_name, workshop, time)
            st.success("Добавлено!")
            st.rerun()


# ✅ Форма добавления/редактирования продукта
def display_product_form():
    is_edit = st.session_state.edit_product_id is not None

    if is_edit:
        st.header("✏️ Редактирование продукта")
        data = db.get_product_by_id(st.session_state.edit_product_id)
    else:
        st.header("➕ Добавление нового продукта")
        data = {}

    types = db.get_unique_product_types()
    materials = db.get_unique_materials()

    with st.form("product_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Название", value=data.get("Product name", ""))
            product_type = st.selectbox("Тип", types, index=types.index(data.get("Product type", types[0])))

        with col2:
            article = st.number_input("Артикул", min_value=1, value=int(data.get("Article", 1)))
            price = st.number_input("Цена", min_value=0.0, value=float(data.get("Minimum cost for a partner", 0.0)))

        material = st.selectbox("Материал", materials, index=materials.index(data.get("Main material", materials[0])))

        submitted = st.form_submit_button("Сохранить")

        if submitted:
            payload = {
                "product_type": product_type,
                "name": name,
                "article": article,
                "min_price": price,
                "main_material": material
            }

            if is_edit:
                db.update_product(st.session_state.edit_product_id, payload)
                st.success("Обновлено!")
            else:
                new_id = db.add_product(payload)
                st.success(f"Добавлено! ID: {new_id}")

            st.session_state.show_add_form = False
            st.session_state.edit_product_id = None
            st.rerun()


# ✅ Страница цехов
def display_workshops_page():
    st.header("🏭 Цеха производства")

    df = db.get_workshops()

    if df.empty:
        st.info("Нет данных о цехах.")
        return

    st.metric("Всего цехов", len(df))
    st.metric("Общее число работников", df["employee_count"].sum())

    st.dataframe(df, hide_index=True, use_container_width=True)


# ✅ Страница расчёта сырья
def display_calculation_page():
    st.header("📐 Калькулятор материалов")

    with st.spinner("Загрузка данных..."):
        product_types_data = db.get_product_types()
        material_types_data = db.get_material_types()

    product_types_options = [pt['name'] for pt in product_types_data]
    product_types_dict = {pt['name']: pt['coefficient'] for pt in product_types_data}

    material_types_options = [mt['name'] for mt in material_types_data]
    material_types_dict = {mt['name']: mt['loss_percent'] for mt in material_types_data}

    param_labels = {
        "Гостиные": ("Площадь (м²)", "Коэффициент плотности"),
        "Прихожие": ("Ширина (м)", "Высота (м)"),
        "Мягкая мебель": ("Объём (м³)", "Коэффициент наполнителя"),
        "Кровати": ("Длина (м)", "Ширина (м)"),
        "Шкафы": ("Ширина (м)", "Высота (м)"),
        "Комоды": ("Площадь фасада (м²)", "Толщина материала (мм)")
    }

    st.markdown("---")
    st.subheader("📝 Параметры расчёта")

    with st.form(key="calculation_form", border=True):
        col1, col2 = st.columns(2)

        with col1:
            selected_product_type = st.selectbox(
                "**Категория изделия**",
                options=product_types_options,
                key="calc_product_type_selectbox"
            )

            quantity = st.number_input(
                "**Количество изделий**",
                min_value=1,
                value=1,
                step=1
            )

        with col2:
            selected_material = st.selectbox(
                "**Материал**",
                options=material_types_options,
                key="calc_material_selectbox"
            )

        param1_label, param2_label = param_labels.get(
            selected_product_type,
            ("Параметр 1", "Параметр 2")
        )

        st.markdown("### 🔧 Производственные параметры")

        col3, col4 = st.columns(2)

        with col3:
            param1 = st.number_input(
                f"**{param1_label}**",
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )

        with col4:
            param2 = st.number_input(
                f"**{param2_label}**",
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )

        submitted = st.form_submit_button("📊 Рассчитать", type="primary")

        if submitted:
            type_coeff = product_types_dict[selected_product_type]
            loss_percent = material_types_dict[selected_material]

            base_raw = param1 * param2 * type_coeff
            total_raw = base_raw * quantity * (1 + loss_percent / 100)

            total_raw = int(total_raw + 0.999)

            st.success(f"✅ Необходимое количество сырья: **{total_raw} ед.**")


# ✅ Рендер страниц
main_header()
sidebar_navigation()

if st.session_state.current_page == "products":
    display_products_page()
elif st.session_state.current_page == "workshops":
    display_workshops_page()
elif st.session_state.current_page == "calculation":
    display_calculation_page()

# ✅ Футер
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center; color:#777; padding:10px;'>© 2006–2025</div>",
    unsafe_allow_html=True
)