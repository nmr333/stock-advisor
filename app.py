import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="المحلل المالي الشامل", layout="wide")

# --- التنسيق (CSS) لتحسين المظهر ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; margin: 10px 0;}
    .stTab {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- القائمة الجانبية ---
st.sidebar.title("🔍 إعدادات البحث")
ticker = st.sidebar.text_input("رمز السهم", value="AAPL").upper()
period = st.sidebar.selectbox("الفترة الزمنية", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
interval = st.sidebar.selectbox("الفاصل الزمني", ["1d", "1wk", "1mo"], index=0)
st.sidebar.markdown("---")
st.sidebar.info("يدعم الأسهم الأمريكية (AAPL)، السعودية (1120.SR)، والعملات الرقمية (BTC-USD).")

# --- دوال التحليل ---
def get_stock_data(symbol, period, interval):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        info = stock.info
        return df, info
    except:
        return None, None

def calculate_all_indicators(df):
    # 1. الاتجاه (Trend)
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.ema(length=12, append=True)
    df.ta.ema(length=26, append=True)
    df.ta.adx(append=True) # قوة الاتجاه

    # 2. الزخم (Momentum)
    df.ta.rsi(length=14, append=True)
    df.ta.macd(append=True) # ينتج عنه 3 أعمدة
    df.ta.stoch(append=True) # الاستوكاستك
    df.ta.cci(length=20, append=True) # مؤشر قناة السلع
    df.ta.willr(append=True) # ويليامز

    # 3. التقلب (Volatility)
    df.ta.bbands(length=20, std=2, append=True) # بولنجر باندز
    df.ta.atr(length=14, append=True) # متوسط المدى الحقيقي

    # 4. الحجم (Volume)
    df.ta.obv(append=True) # الحجم التراكمي
    
    return df

# --- التطبيق الرئيسي ---
st.title(f"📊 التقرير الشامل للسهم: {ticker}")

if ticker:
    with st.spinner('جاري جلب وتحليل جميع البيانات...'):
        df, info = get_stock_data(ticker, period, interval)

        if df is not None and not df.empty:
            df = calculate_all_indicators(df)
            
            # تقسيم الصفحة إلى تبويبات
            tab1, tab2, tab3, tab4 = st.tabs(["🏠 نظرة عامة", "📈 التحليل الفني المتقدم", "💰 البيانات المالية", "🗂 البيانات التاريخية"])

            # ================= TAB 1: نظرة عامة =================
            with tab1:
                # الصف الأول: السعر والتغير
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change = current_price - prev_price
                pct_change = (change / prev_price) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("السعر الحالي", f"{current_price:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
                col2.metric("أعلى سعر (52 أسبوع)", info.get('fiftyTwoWeekHigh', 'N/A'))
                col3.metric("أدنى سعر (52 أسبوع)", info.get('fiftyTwoWeekLow', 'N/A'))
                col4.metric("حجم التداول", f"{df['Volume'].iloc[-1]:,}")

                # رسم بياني تفاعلي (شموع يابانية)
                st.subheader("الرسم البياني (Candlestick Chart)")
                fig = go.Figure(data=[go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name='السعر')])
                fig.update_layout(xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            # ================= TAB 2: التحليل الفني =================
            with tab2:
                st.header("لوحة المؤشرات الفنية")
                
                # إشارات البيع والشراء بناءً على المؤشرات
                latest = df.iloc[-1]
                
                # تجهيز الإشارات
                signals = []
                # RSI
                if latest['RSI_14'] < 30: signals.append("RSI: شراء (تشبع بيعي) 🟢")
                elif latest['RSI_14'] > 70: signals.append("RSI: بيع (تشبع شرائي) 🔴")
                else: signals.append("RSI: محايد ⚪")
                
                # SMA Trend
                if latest['Close'] > latest['SMA_200']: signals.append("الترند العام: صاعد (فوق متوسط 200) 🟢")
                else: signals.append("الترند العام: هابط (تحت متوسط 200) 🔴")

                # MACD
                if latest['MACD_12_26_9'] > latest['MACDs_12_26_9']: signals.append("MACD: تقاطع إيجابي (شراء) 🟢")
                else: signals.append("MACD: تقاطع سلبي (بيع) 🔴")

                # عرض الإشارات في مربعات ملونة
                st.subheader("🤖 ملخص إشارات الذكاء الاصطناعي")
                c1, c2 = st.columns(2)
                for i, sig in enumerate(signals):
                    if i % 2 == 0: c1.success(sig) if "🟢" in sig else c1.error(sig) if "🔴" in sig else c1.info(sig)
                    else: c2.success(sig) if "🟢" in sig else c2.error(sig) if "🔴" in sig else c2.info(sig)

                st.markdown("---")
                
                # الرسوم البيانية للمؤشرات
                st.subheader("1. المتوسطات المتحركة (SMA/EMA)")
                st.line_chart(df[['Close', 'SMA_50', 'SMA_200']])
                
                col_tech1, col_tech2 = st.columns(2)
                with col_tech1:
                    st.subheader("2. مؤشر القوة النسبية (RSI)")
                    st.line_chart(df['RSI_14'])
                with col_tech2:
                    st.subheader("3. مؤشر الماكد (MACD)")
                    st.line_chart(df[['MACD_12_26_9', 'MACDs_12_26_9']])

                st.subheader("4. نطاقات بولنجر (Bollinger Bands)")
                st.line_chart(df[['BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0']])

            # ================= TAB 3: البيانات المالية =================
            with tab3:
                st.header("البيانات الأساسية للشركة")
                
                f_col1, f_col2, f_col3 = st.columns(3)
                
                with f_col1:
                    st.markdown("### 🏢 التقييم")
                    st.write(f"**القيمة السوقية:** {info.get('marketCap', 'N/A')}")
                    st.write(f"**مكرر الربحية (P/E):** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**مكرر الربحية المستقبلي (Forward P/E):** {info.get('forwardPE', 'N/A')}")
                    st.write(f"**نسبة النمو (PEG):** {info.get('pegRatio', 'N/A')}")
                    st.write(f"**السعر للقيمة الدفترية (P/B):** {info.get('priceToBook', 'N/A')}")

                with f_col2:
                    st.markdown("### 💰 الربحية والعوائد")
                    st.write(f"**هامش الربح:** {info.get('profitMargins', 0)*100:.2f}%")
                    st.write(f"**العائد على الأصول (ROA):** {info.get('returnOnAssets', 0)*100:.2f}%")
                    st.write(f"**العائد على الحقوق (ROE):** {info.get('returnOnEquity', 0)*100:.2f}%")
                    st.write(f"**توزيعات الأرباح (Yield):** {info.get('dividendYield', 0)*100:.2f}%")

                with f_col3:
                    st.markdown("### 🏦 الديون والنقد")
                    st.write(f"**إجمالي الكاش:** {info.get('totalCash', 'N/A')}")
                    st.write(f"**إجمالي الديون:** {info.get('totalDebt', 'N/A')}")
                    st.write(f"**نسبة الدين للكاش:** {info.get('debtToEquity', 'N/A')}")
                    st.write(f"**التدفق النقدي الحر:** {info.get('freeCashflow', 'N/A')}")
                
                st.markdown("---")
                st.markdown("### 📋 وصف النشاط")
                st.write(info.get('longBusinessSummary', 'لا يوجد وصف متاح.'))

            # ================= TAB 4: الجدول التاريخي =================
            with tab4:
                st.header("سجل البيانات بالكامل")
                # زر لتحميل البيانات
                @st.cache_data
                def convert_df(df):
                    return df.to_csv().encode('utf-8')

                csv = convert_df(df)
                st.download_button(
                    label="📥 تحميل البيانات كملف Excel/CSV",
                    data=csv,
                    file_name=f'{ticker}_data.csv',
                    mime='text/csv',
                )
                
                st.dataframe(df.sort_index(ascending=False))

        else:
            st.error("الرمز غير صحيح أو لا توجد بيانات متاحة.")
