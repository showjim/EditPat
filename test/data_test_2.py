"""
data_editor.py
"""

import pandas as pd

import streamlit as st


TRACES = ['Bar', 'Line']
Y_VALUES = ['y', 'y-y0', '(y-y0)/y0', 'y/y0']

df = pd.DataFrame({
    'column': ['Volume', 'Amount', 'PE', 'PE TTM', 'PB', 'PS', 'PS TTM', 'DV Ratio', 'DV TTM'],
    'show': [True, False, True, False, False, False, False, False, False],
    'trace': ['Bar', 'Bar', 'Line', 'Line', 'Line', 'Line', 'Line', 'Line', 'Line'],
    'y_value': ['y', 'y', 'y', 'y', 'y', 'y', 'y', 'y', 'y'],
    'height': [100, 100, 100, 100, 100, 100, 100, 100, 100],
    'description': ['成交量(手)', '成交额(千元)', '市盈率', '市盈率TTM', '市净率', '市销率', '市销率TTM', '股息率(%)', '股息率TTM(%)']
})


EDITOR_KEY_PREFIX = '__'


def data_editor_key(key):
    """Gets data_editor key based on a value_key. """
    return EDITOR_KEY_PREFIX + key


def data_editor_change(key, editor_key):
    """Callback function of data_editor. """
    st.session_state[key] = apply_de_change(st.session_state[key], st.session_state[editor_key])


def apply_de_change(df0, changes):
    """Apply changes of data_editor."""
    add_rows = changes.get('added_rows')
    edited_rows = changes.get('edited_rows')
    deleted_rows = changes.get('deleted_rows')

    for idx, row in edited_rows.items():
        for name, value in row.items():
            df0.loc[df0.index[idx], name] = value

    df0.drop(df0.index[deleted_rows], inplace=True)

    ss = []
    has_index = add_rows and '_index' in add_rows[0]
    for add_row in add_rows:
        if '_index' in add_row:
            ss.append(pd.Series(data=add_row, name=add_row.pop('_index')))
        else:
            ss.append(pd.Series(data=add_row))
    df_add = pd.DataFrame(ss)

    return pd.concat([df0, df_add], axis=0) if has_index else pd.concat([df0, df_add], axis=0, ignore_index=True)


df_key = 'my_def'                            # value_key of data_editor
df_editor_key = data_editor_key(df_key)      # editor_key of data_editor
if df_key not in st.session_state:           # initialize session_state.value_key
    st.session_state[df_key] = df


with st.expander('股票趋势'):
    c1, c2, c3 = st.columns([1, 12, 1])
    with c2:
        column1, column2, column3 = st.columns([4, 2, 4])

        with column1:
            st.selectbox('股票价格', ['线图', 'k线图'])

        with column3:
            st.selectbox('复权', ['不复权', '前复权', '后复权'])

        st.text('主要指标')
        chart_df = st.data_editor(
            st.session_state[df_key].copy(),
            key=df_editor_key,                       # set editor_key
            on_change=data_editor_change,            # callback function
            args=(df_key, df_editor_key),
            column_config={
                'column': st.column_config.Column(
                    'column',
                    required=True,
                    disabled=False),
                'show': st.column_config.CheckboxColumn(
                    "show",
                    # width="small",
                    default=False),
                'trace': st.column_config.SelectboxColumn(
                    "trace",
                    # width="small",
                    options=TRACES,
                    default=TRACES[0],
                    required=True),
                'y_value': st.column_config.SelectboxColumn(
                    "y_f",
                    options=Y_VALUES,
                    default=Y_VALUES[0],
                    required=True),
                'height': st.column_config.NumberColumn("height",
                                                        width='small',
                                                        required=True,
                                                        default=100,
                                                        min_value=50, max_value=300),
                'description': st.column_config.Column(
                    'desc',
                    disabled=False)
            },
            num_rows='dynamic',
            use_container_width=True,
            height=450,
            hide_index=True)
    st.write('')


