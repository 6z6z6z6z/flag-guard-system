"""
包含系统使用的所有SQL查询语句
"""

# 用户相关查询
USER_QUERIES = {
    'get_by_id': """
        SELECT * FROM users WHERE user_id = %s
    """,
    'get_by_username': """
        SELECT * FROM users WHERE username = %s
    """,
    'get_by_student_id': """
        SELECT * FROM users WHERE student_id = %s
    """,
    'create': """
        INSERT INTO users (username, password, role, name, student_id, college, phone_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
    'update': """
        UPDATE users
        SET name = %s, college = %s, role = %s, phone_number = %s, height = %s, weight = %s, shoe_size = %s
        WHERE user_id = %s
    """,
    'update_password': """
        UPDATE users SET password = %s WHERE user_id = %s
    """,
    'update_points': """
        UPDATE users SET total_points = total_points + %s WHERE user_id = %s
    """,
    'delete': """
        DELETE FROM users WHERE user_id = %s
    """,
    'list_all': """
        SELECT user_id, username, role, name, student_id, college, total_points, phone_number, height, weight, shoe_size
        FROM users
    """,
    'search': """
        SELECT user_id, username, role, name, student_id, college, total_points, phone_number, height, weight, shoe_size
        FROM users
        WHERE username LIKE %s OR name LIKE %s OR student_id LIKE %s
    """
}

# 训练相关查询
TRAINING_QUERIES = {
    'create': """
        INSERT INTO trainings (name, start_time, end_time, points, location, created_by, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
    'get_by_id': """
        SELECT * FROM trainings WHERE training_id = %s
    """,
    'update': """
        UPDATE trainings 
        SET name = %s, start_time = %s, end_time = %s, points = %s, location = %s, status = %s 
        WHERE training_id = %s
    """,
    'delete': """
        DELETE FROM trainings WHERE training_id = %s
    """,
    'list_all': """
        SELECT t.*, u.name as creator_name 
        FROM trainings t
        LEFT JOIN users u ON t.created_by = u.user_id
        ORDER BY t.start_time DESC
    """,
    'list_upcoming': """
        SELECT t.*, u.name as creator_name 
        FROM trainings t
        LEFT JOIN users u ON t.created_by = u.user_id
        WHERE t.start_time > NOW()
        ORDER BY t.start_time ASC
    """,
    'update_status': """
        UPDATE trainings SET status = %s WHERE training_id = %s
    """
}

# 训练报名相关查询
TRAINING_REGISTRATION_QUERIES = {
    'create': """
        INSERT INTO training_registrations (training_id, user_id, status)
        VALUES (%s, %s, %s)
    """,
    'get_by_id': """
        SELECT * FROM training_registrations WHERE registration_id = %s
    """,
    'get_by_training_and_user': """
        SELECT * FROM training_registrations 
        WHERE training_id = %s AND user_id = %s
    """,
    'update_status': """
        UPDATE training_registrations 
        SET status = %s, attendance_status = %s
        WHERE registration_id = %s
    """,
    'award_points': """
        UPDATE training_registrations
        SET points_awarded = %s, status = 'awarded'
        WHERE registration_id = %s
    """,
    'delete': """
        DELETE FROM training_registrations WHERE registration_id = %s
    """,
    'list_by_training': """
        SELECT tr.*, u.name, u.student_id, u.college, u.username, u.phone_number
        FROM training_registrations tr
        JOIN users u ON tr.user_id = u.user_id
        WHERE tr.training_id = %s
        ORDER BY tr.created_at ASC
    """,
    'list_by_user': """
        SELECT tr.*, t.name as training_name, t.start_time, t.end_time, t.location, t.status as training_status
        FROM training_registrations tr
        JOIN trainings t ON tr.training_id = t.training_id
        WHERE tr.user_id = %s
        ORDER BY t.start_time DESC
    """
}

# 活动相关查询
EVENT_QUERIES = {
    'create': """
        INSERT INTO events (name, time, location, uniform_required, created_by)
        VALUES (%s, %s, %s, %s, %s)
    """,
    'get_by_id': """
        SELECT * FROM events WHERE event_id = %s
    """,
    'update': """
        UPDATE events
        SET name = %s, time = %s, location = %s, uniform_required = %s
        WHERE event_id = %s
    """,
    'delete': """
        DELETE FROM events WHERE event_id = %s
    """,
    'list_all': """
        SELECT e.*, u.name as creator_name
        FROM events e
        LEFT JOIN users u ON e.created_by = u.user_id
        ORDER BY e.time DESC
    """,
    'list_upcoming': """
        SELECT e.*, u.name as creator_name
        FROM events e
        LEFT JOIN users u ON e.created_by = u.user_id
        WHERE e.time > NOW()
        ORDER BY e.time ASC
    """
}

# 活动-训练关联查询
EVENT_TRAINING_QUERIES = {
    'add': """
        INSERT INTO event_trainings (event_id, training_id)
        VALUES (%s, %s)
    """,
    'remove': """
        DELETE FROM event_trainings WHERE event_id = %s AND training_id = %s
    """,
    'list_by_event': """
        SELECT t.*
        FROM event_trainings et
        JOIN trainings t ON et.training_id = t.training_id
        WHERE et.event_id = %s
    """,
    'list_by_training': """
        SELECT e.*
        FROM event_trainings et
        JOIN events e ON et.event_id = e.event_id
        WHERE et.training_id = %s
    """
}

# 活动报名相关查询
EVENT_REGISTRATION_QUERIES = {
    'create': """
        INSERT INTO event_registrations (event_id, user_id, status)
        VALUES (%s, %s, %s)
    """,
    'get_by_id': """
        SELECT * FROM event_registrations WHERE registration_id = %s
    """,
    'get_by_event_and_user': """
        SELECT * FROM event_registrations 
        WHERE event_id = %s AND user_id = %s
    """,
    'update_status': """
        UPDATE event_registrations 
        SET status = %s
        WHERE registration_id = %s
    """,
    'delete': """
        DELETE FROM event_registrations WHERE registration_id = %s
    """,
    'list_by_event': """
        SELECT er.*, u.name, u.student_id, u.college, u.username, u.phone_number, 
               u.height, u.weight, u.shoe_size
        FROM event_registrations er
        JOIN users u ON er.user_id = u.user_id
        WHERE er.event_id = %s
        ORDER BY er.created_at ASC
    """,
    'list_by_user': """
        SELECT er.*, e.name as event_name, e.time, e.location
        FROM event_registrations er
        JOIN events e ON er.event_id = e.event_id
        WHERE er.user_id = %s
        ORDER BY e.time DESC
    """
}

# 升降旗记录相关查询
FLAG_RECORD_QUERIES = {
    'create': """
        INSERT INTO flag_records (user_id, date, type, photo_url, status)
        VALUES (%s, %s, %s, %s, %s)
    """,
    'get_by_id': """
        SELECT fr.*, 
               u1.name as user_name, 
               u1.student_id,
               u2.name as reviewer_name
        FROM flag_records fr
        LEFT JOIN users u1 ON fr.user_id = u1.user_id
        LEFT JOIN users u2 ON fr.reviewer_id = u2.user_id
        WHERE fr.record_id = %s
    """,
    'update': """
        UPDATE flag_records
        SET date = %s, type = %s, photo_url = %s
        WHERE record_id = %s
    """,
    'review': """
        UPDATE flag_records
        SET status = %s, points_awarded = %s, reviewer_id = %s, reviewed_at = NOW()
        WHERE record_id = %s
    """,
    'delete': """
        DELETE FROM flag_records WHERE record_id = %s
    """,
    'list_by_user': """
        SELECT fr.*, 
               u2.name as reviewer_name
        FROM flag_records fr
        LEFT JOIN users u2 ON fr.reviewer_id = u2.user_id
        WHERE fr.user_id = %s
        ORDER BY fr.date DESC
    """,
    'list_all': """
        SELECT fr.*, 
               u1.name as user_name, 
               u1.student_id, 
               u2.name as reviewer_name,
               CASE 
                   WHEN fr.status = 'pending' THEN 'pending'
                   WHEN fr.status = 'approved' THEN 'approved'
                   WHEN fr.status = 'rejected' THEN 'rejected'
                   ELSE 'pending'
               END as status_text
        FROM flag_records fr
        JOIN users u1 ON fr.user_id = u1.user_id
        LEFT JOIN users u2 ON fr.reviewer_id = u2.user_id
        ORDER BY fr.date DESC
    """,
    'list_pending': """
        SELECT fr.*, 
               u1.name as user_name, 
               u1.student_id
        FROM flag_records fr
        JOIN users u1 ON fr.user_id = u1.user_id
        WHERE fr.status = 'pending'
        ORDER BY fr.date ASC
    """
}

# 积分历史相关查询
POINT_HISTORY_QUERIES = {
    'create': """
        INSERT INTO point_history (user_id, points_change, change_type, description, related_id)
        VALUES (%s, %s, %s, %s, %s)
    """,
    'get_by_id': """
        SELECT * FROM point_history WHERE history_id = %s
    """,
    'list_by_user': """
        SELECT * FROM point_history
        WHERE user_id = %s
        ORDER BY change_time DESC
    """,
    'list_all': """
        SELECT ph.*, u.name, u.student_id
        FROM point_history ph
        JOIN users u ON ph.user_id = u.user_id
        ORDER BY ph.change_time DESC
    """,
    'get_user_total': """
        SELECT SUM(points_change) as total_points
        FROM point_history
        WHERE user_id = %s
    """
}

# 操作日志相关查询
OPERATION_LOG_QUERIES = {
    'create': """
        INSERT INTO operation_logs (user_id, endpoint, method, ip_address)
        VALUES (%s, %s, %s, %s)
    """,
    'list_recent': """
        SELECT ol.*, u.username
        FROM operation_logs ol
        LEFT JOIN users u ON ol.user_id = u.user_id
        ORDER BY ol.timestamp DESC
        LIMIT %s
    """
}

# 统计查询
STATS_QUERIES = {
    'user_count': """
        SELECT COUNT(*) as total FROM users
    """,
    'training_count': """
        SELECT COUNT(*) as total FROM trainings
    """,
    'event_count': """
        SELECT COUNT(*) as total FROM events
    """,
    'flag_count': """
        SELECT COUNT(*) as total FROM flag_records
    """,
    'top_users_by_points': """
        SELECT user_id, username, name, student_id, college, total_points
        FROM users
        ORDER BY total_points DESC
        LIMIT %s
    """,
    'recent_activities': """
        SELECT 
            'training' as type, 
            t.name as name, 
            t.start_time as time, 
            COUNT(tr.registration_id) as participants
        FROM trainings t
        LEFT JOIN training_registrations tr ON t.training_id = tr.training_id
        WHERE t.start_time <= NOW()
        GROUP BY t.training_id
        UNION ALL
        SELECT 
            'event' as type, 
            e.name as name, 
            e.time as time, 
            COUNT(er.registration_id) as participants
        FROM events e
        LEFT JOIN event_registrations er ON e.event_id = er.event_id
        WHERE e.time <= NOW()
        GROUP BY e.event_id
        ORDER BY time DESC
        LIMIT %s
    """
} 