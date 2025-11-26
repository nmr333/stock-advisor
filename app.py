import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- إعدادات الصفحة ---
st.set_page_config(page_title="المستشار المالي الذكي", layout="wide")

# عنوان التطبيق
st.title("📈 المستشار المالي الذكي للأسهم")
st.markdown("---")

# --- القائمة الجانبية للإدخال ---
st.sidebar.header("إعدادات البحث")
ticker = st.sidebar.text_input("أدخل رمز السهم (مثلاً AAPL, TSLA, 1120.SR)", value="AAPL").upper()
btn_analyze = st.sidebar.button("حلل السهم الآن")

# --- دالة التحليل ---
def analyze_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        info = stock.info
        
        if df.empty:
            st.error("لم يتم العثور على بيانات لهذا السهم. تأكد من الرمز.")
            return None

        # حساب المؤشرات الفنية
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        # التقييم
        current_price = df['Close'].iloc[-1]
        pe = info.get('trailingPE', 'N/A')
        rsi = df['RSI'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        
        return {
            "price": current_price,
            "pe": pe,
            "rsi": rsi,
            "sma_200": sma_200,
            "df": df,
            "name": info.get('longName', symbol)
        }
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return None

# --- عرض النتائج عند الضغط على الزر ---
if btn_analyze:
    with st.spinner('جاري تحليل البيانات...'):
        data = analyze_stock(ticker)
        
        if data:
            # 1. عرض المعلومات الأساسية
            st.subheader(f"التقرير المالي لشركة: {data['name']}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("السعر الحالي", f"${data['price']:.2f}")
            col2.metric("مكرر الربحية (P/E)", data['pe'])
            col3.metric("مؤشر القوة (RSI)", f"{data['rsi']:.1f}")
            
            trend = "اتجاه صاعد 🟢" if data['price'] > data['sma_200'] else "اتجاه هابط 🔴"
            col4.metric("الاتجاه العام", trend)

            # 2. نصيحة البوت
            st.markdown("### 🤖 رأي المستشار الآلي:")
            if data['rsi'] < 30:
                st.success("الأسعار مغرية للشراء (تشبع بيعي)! 🚀")
            elif data['rsi'] > 70:
                st.warning("الأسعار مرتفعة جداً (تشبع شرائي)، انتبه! ⚠️")
            else:
                st.info("السعر في مناطق محايدة، يفضل الانتظار. ✋")

            # 3. الرسم البياني
            st.markdown("### 📊 حركة السعر")
            st.line_chart(data['df']['Close'])

            # 4. الجدول
            st.markdown("### 📑 آخر 5 أيام تداول")
            st.dataframe(data['df'].tail(5))
