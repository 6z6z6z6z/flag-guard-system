import pandas as pd
from flask import send_file
from io import BytesIO

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
    from models import PointHistory
    data = PointHistory.query.filter_by(user_id=user_id).all()
    records = [{
        '时间': item.change_time.strftime('%Y-%m-%d %H:%M'),
        '积分变动': item.points_change,
        '类型': item.change_type,
        '描述': item.description
    } for item in data]
    return export_to_excel(records, f'user_{user_id}_points_history')