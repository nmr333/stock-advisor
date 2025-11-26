import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# --- إعدادات الصفحة ---
st.set_page_config(page_title="المحلل المالي الشامل", layout="wide")

# --- التنسيق (CSS) ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; margin: 10px 0;}
    .stTab {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- القائمة الجانبية ---
st.sidebar.title("🔍 إعدادات البحث")
ticker = st.sidebar.text_input("رمز السهم", value="AAPL").upper()
# جعلنا الفترة الافتراضية "سنتين" لضمان عمل المؤشرات الطويلة
period = st.sidebar.selectbox("الفترة الزمنية", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=4) 
interval = st.sidebar.selectbox("الفاصل الزمني", ["1d", "1wk", "1mo"], index=0)
st.sidebar.markdown("---")
st.sidebar.info("ملاحظة: لحساب متوسط 200 يوم، يجب أن تكون البيانات المحملة أكثر من 200 يوم تداول.")

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
    # لا نقوم بالحساب إلا إذا توفرت بيانات كافية (الحماية من الأخطاء)
    if len(df) >= 20:
        df.ta.sma(length=20, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.cci(length=20, append=True)
    
    if len(df) >= 50:
        df.ta.sma(length=50, append=True)
    
    if len(df) >= 200:
        df.ta.sma(length=200, append=True)

    if len(df) >= 14:
        df.ta.rsi(length=14, append=True)
        df.ta.adx(append=True)
        df.ta.atr(length=14, append=True)
        df.ta.willr(append=True)

    if len(df) >= 26:
        df.ta.macd(append=True)

    df.ta.stoch(append=True)
    df.ta.obv(append=True)
    
    return df

# --- التطبيق الرئيسي ---
st.title(f"📊 التقرير الشامل للسهم: {ticker}")

if ticker:
    with st.spinner('جاري جلب وتحليل البيانات...'):
        df, info = get_stock_data(ticker, period, interval)

        if df is not None and not df.empty:
            df = calculate_all_indicators(df)
            
            # تجهيز المتغيرات بشكل آمن (Defensive Coding)
            latest = df.iloc[-1]
            cols = df.columns # قائمة أسماء الأعمدة الموجودة فعلياً
            
            # التبويبات
            tab1, tab2, tab3, tab4 = st.tabs(["🏠 نظرة عامة", "📈 التحليل الفني", "💰 البيانات المالية", "🗂 السجل"])

            # ================= TAB 1: نظرة عامة =================
            with tab1:
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change = current_price - prev_price
                pct_change = (change / prev_price) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("السعر الحالي", f"{current_price:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
                col2.metric("أعلى سعر (52 أسبوع)", info.get('fiftyTwoWeekHigh', 'N/A'))
                col3.metric("أدنى سعر (52 أسبوع)", info.get('fiftyTwoWeekLow', 'N/A'))
                col4.metric("حجم التداول", f"{latest['Volume']:,}")

                st.subheader("الرسم البياني")
                fig = go.Figure(data=[go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name='السعر')])
                fig.update_layout(xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            # ================= TAB 2: التحليل الفني =================
            with tab2:
                st.header("لوحة المؤشرات الفنية")
                
                signals = []
                
                # فحص وجود الأعمدة قبل قراءتها لتجنب KeyError
                # 1. RSI
                if 'RSI_14' in cols and not pd.isna(latest['RSI_14']):
                    rsi = latest['RSI_14']
                    if rsi < 30: signals.append(f"RSI ({rsi:.1f}): شراء (تشبع بيعي) 🟢")
                    elif rsi > 70: signals.append(f"RSI ({rsi:.1f}): بيع (تشبع شرائي) 🔴")
                    else: signals.append(f"RSI ({rsi:.1f}): محايد ⚪")

                # 2. SMA 200 (هنا كان الخطأ السابق)
                if 'SMA_200' in cols and not pd.isna(latest['SMA_200']):
                    if latest['Close'] > latest['SMA_200']: 
                        signals.append("الترند العام: صاعد (فوق متوسط 200) 🟢")
                    else: 
                        signals.append("الترند العام: هابط (تحت متوسط 200) 🔴")
                else:
                    signals.append("الترند العام: بيانات غير كافية للحساب ⚠️")

                # 3. MACD
                if 'MACD_12_26_9' in cols and 'MACDs_12_26_9' in cols:
                    if latest['MACD_12_26_9'] > latest['MACDs_12_26_9']: 
                        signals.append("MACD: تقاطع إيجابي (شراء) 🟢")
                    else: 
                        signals.append("MACD: تقاطع سلبي (بيع) 🔴")

                # عرض الإشارات
                st.subheader("🤖 إشارات الذكاء الاصطناعي")
                if signals:
                    c1, c2 = st.columns(2)
                    for i, sig in enumerate(signals):
                        # توزيع الإشارات على عمودين
                        target_col = c1 if i % 2 == 0 else c2
                        if "🟢" in sig: target_col.success(sig)
                        elif "🔴" in sig: target_col.error(sig)
                        else: target_col.info(sig)
                else:
                    st.warning("لا توجد بيانات كافية لإصدار إشارات فنية.")

                st.markdown("---")
                
                # الرسوم البيانية (نعرض فقط الموجود)
                st.subheader("المتوسطات المتحركة")
                available_smas = ['Close']
                if 'SMA_50' in cols: available_smas.append('SMA_50')
                if 'SMA_200' in cols: available_smas.append('SMA_200')
                st.line_chart(df[available_smas])

            # ================= TAB 3: البيانات المالية =================
            with tab3:
                st.header("البيانات الأساسية")
                f1, f2, f3 = st.columns(3)
                with f1:
                    st.markdown("### 🏢 التقييم")
                    st.write(f"**القيمة السوقية:** {info.get('marketCap', 'N/A')}")
                    st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                with f2:
                    st.markdown("### 💰 العوائد")
                    st.write(f"**ROE:** {info.get('returnOnEquity', 0)*100:.2f}%")
                    st.write(f"**توزيعات الأرباح:** {info.get('dividendYield', 0)*100:.2f}%")
                with f3:
                    st.markdown("### 🏦 الميزانية")
                    st.write(f"**الديون:** {info.get('totalDebt', 'N/A')}")
                    st.write(f"**الكاش:** {info.get('totalCash', 'N/A')}")
                
                st.markdown("---")
                st.write(f"**نبذة:** {info.get('longBusinessSummary', 'غير متاح')}")

            # ================= TAB 4: السجل =================
            with tab4:
                st.header("البيانات التاريخية")
                @st.cache_data
                def convert_df(df):
                    return df.to_csv().encode('utf-8')
                csv = convert_df(df)
                st.download_button("📥 تحميل CSV", csv, f'{ticker}_data.csv', 'text/csv')
                st.dataframe(df.sort_index(ascending=False))

        else:
            st.error("الرمز غير صحيح أو لا توجد بيانات.")

