<template>
  <div class="users-container">
    <div class="header-controls">
      <h1 class="page-title">用户管理</h1>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户（用户名/姓名/学号）"
          aria-label="搜索用户"
          class="search-input"
          @input="handleSearch"
        />
        <!-- <el-button type="primary" @click="handleCreate">
          创建用户
        </el-button> -->
      </div>
    </div>
    <el-divider />

    <el-table :data="users" style="width: 100%" v-loading="loading">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="student_id" label="学号" />
      <el-table-column prop="college" label="学院" />
      <el-table-column prop="phone_number" label="手机号" />
      <el-table-column prop="role" label="角色">
        <template #default="{ row }">
          <el-tag :type="getRoleTagType(row.role)">
            {{ getRoleText(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="total_points" label="积分" sortable>
        <template #default="{ row }">
          <span>{{ row.total_points || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button-group v-if="isSuperAdmin || isAdmin">
            <el-button 
              type="primary" 
              size="small" 
              @click="handleEdit(row)"
              v-if="isSuperAdmin || isAdmin"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              v-if="isSuperAdmin"
            >
              删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="学号" prop="student_id">
          <el-input v-model="form.student_id" />
        </el-form-item>
        <el-form-item label="学院" prop="college">
          <el-input v-model="form.college" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone_number">
          <el-input v-model="form.phone_number" />
        </el-form-item>
        <el-form-item label="角色" prop="role" v-if="isSuperAdmin">
          <el-select 
            v-model="form.role" 
            style="width: 100%" 
            placeholder="选择角色"
            :disabled="form.id === userStore.userInfo?.id"
          >
            <el-option label="管理员" value="admin" />
            <el-option label="队员" value="member" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'
import type { FormInstance } from 'element-plus'
import { useUserStore } from '@/stores/user'

const getRoleText = (role: string) => {
  switch (role) {
    case 'superadmin':
      return '超级管理员'
    case 'admin':
      return '管理员'
    case 'member':
      return '队员'
    default:
      return '未知'
  }
}

const getRoleTagType = (role: string) => {
  switch (role) {
    case 'superadmin':
      return 'danger'
    case 'admin':
      return 'warning'
    case 'member':
      return 'info'
    default:
      return ''
  }
}

const userStore = useUserStore()
const isSuperAdmin = computed(() => userStore.userInfo?.role === 'superadmin')
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')

interface User {
  user_id: number
  username: string
  name: string
  student_id: string
  college: string
  role: string
  total_points: number
  phone_number: string
}

const users = ref<User[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchQuery = ref('')
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const form = ref({
  id: null,
  username: '',
  name: '',
  password: '',
  student_id: '',
  college: '',
  role: 'member',
  points: 0,
  phone_number: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  student_id: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  college: [{ required: true, message: '请输入学院', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  phone_number: [{ required: true, message: '请输入手机号', trigger: 'blur' }, { pattern: /^\d{11}$/, message: '手机号格式不正确', trigger: 'blur' }]
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await request.get('/users/points/all', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        query: searchQuery.value
      }
    })
    
    if (response.data?.items) {
      users.value = response.data.items
      total.value = response.data.total
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchUsers()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchUsers()
}

// // 创建用户
// const handleCreate = () => {
//   dialogTitle.value = '创建用户'
//   form.value = {
//     id: null,
//     username: '',
//     name: '',
//     password: '',
//     student_id: '',
//     college: '',
//     role: 'member',
//     points: 0,
//     phone_number: ''
//   }
//   dialogVisible.value = true
// }

// 编辑用户
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑用户'
  form.value = { 
    id: row.user_id, 
    username: row.username,
    name: row.name,
    password: '',
    student_id: row.student_id,
    college: row.college,
    role: row.role,
    points: row.total_points || 0,
    phone_number: row.phone_number }
  dialogVisible.value = true
}

// 删除用户
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个用户吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/users/${row.user_id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    // 只有 superadmin 可以修改角色
    if (isSuperAdmin.value && form.value.role !== users.value.find(u => u.user_id === form.value.id)?.role) {
      await request.put(`/users/${form.value.id}/role`, { role: form.value.role })
    }

    // 更新其他信息
    const { username, name, student_id, college, phone_number, password } = form.value
    const payload: any = { username, name, student_id, college, phone_number, password }
    
    // 如果不是 superadmin，则不应发送角色信息
    if (!isSuperAdmin.value) {
      delete payload.role
    }

    const response = await request.put(`/users/${form.value.id}`, payload)

    if (response.code === 200) {
      ElMessage.success('更新成功')
    } else {
      ElMessage.error(response.msg || '更新失败')
    }

    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    console.error('Submit error:', error)
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.users-container {
  padding: 20px;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  margin: 0;
}

.search-input {
  width: 250px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>