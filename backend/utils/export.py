import pandas as pd
from flask import send_file
from io import BytesIO
from models_pymysql import PointHistory
from datetime import datetime

def export_to_excel(data, filename):
    df = pd.DataFrame(data)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False)
    writer.close()
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{filename}.xlsx'
    )


def export_points_history(user_id):
    data = PointHistory.list_by_user(int(user_id))
    records = [{
        '时间': item.get('change_time').strftime('%Y-%m-%d %H:%M') if isinstance(item.get('change_time'), datetime) else item.get('change_time'),
        '积分变动': float(item.get('points_change', 0)),
        '类型': item.get('change_type'),
        '描述': item.get('description')
    } for item in data]
    return export_to_excel(records, f'user_{user_id}_points_history')