import streamlit as st

st.set_page_config(page_title="Home", page_icon="🏡")

st.title('Home🏡')

st.markdown('##  :green[*Street Fighter*]')
st.write('---')

images = [
    ('image/リュウ.jpg', 'リュウ'),
    ('image/ガイル.jpg', 'ガイル'),
    ('image/ザンギエフ.jpg', 'ザンギエフ'),
    ('image/バルログ.jpg', 'バルログ'),
    ('image/ブランカ.jpg', 'ブランカ'),
    ('image/ベガ.jpg', 'ベガ'),
    ('image/春麗.jpg', '春麗'),
    ('image/本田.jpg', '本田'),
    ('image/ネカリ.jpg', 'ネカリ')
]

# 3列に分けて表示
for i in range(0, len(images), 3):
    cols = st.columns(3)
    for col, (img, cap) in zip(cols, images[i:i+3]):
        col.image(img, caption=cap, width=200)

st.video("https://www.youtube.com/watch?v=b0uHA68Yoao")
st.video("https://www.youtube.com/watch?v=Hb1_cZHzQD8")