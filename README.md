Okay, let's provide a comprehensive document including views, templates, and forms for all aspects of the NDE Internal Management System. We'll also explore how the IT Admin team can manage the system and ensure dark mode is considered in the design.

---

## NDE Internal Management System - Design Document

### 1. Introduction

This document outlines the detailed design of the NDE Internal Management System, encompassing views, templates, forms, and management considerations for the IT Admin team. It also considers the inclusion of a dark mode theme for improved user experience.

### 2. System Architecture

The system is structured around five core applications:

1. **Core:** User authentication, authorization, system configuration, and dashboard framework.
2. **Human Resources (HR):** Employee lifecycle management, data management, and reporting.
3. **Programs & Projects:** Program/project creation, management, collaboration, workflows, and reporting.
4. **Finance & Accounts:** Budget, expense, revenue, asset management, and reporting.
5. **Monitoring & Evaluation:** Inspection management, compliance tracking, program verification, and reporting.


### 3. User Roles & Access

The system supports a hierarchical structure of user roles:

- **Director General (DG):** Full system access and permissions management.
- **Director:** Access to their directorate, with management permissions.
- **Zonal Director:** Access to their zone, with management permissions.
- **Head of Department:** Access to their department, with management permissions.
- **State Director:** Access to their state, with management permissions.
- **LGA Liaison Officer:** Limited access for reporting within their LGA.
- **Staff:** General access with role-based permissions.


### 4. App Views, Templates, and Forms

#### 4.1 Core App

**4.1.1 Login (`core:login`)**

- **Template:** `core/templates/login.html`
- **Form:** `core/forms/login_form.py`

```html
<!-- core/templates/login.html -->
<!DOCTYPE html>
<html>
<head>
  <title>NDE Login</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'core/css/styles.css' %}"> 
</head>
<body>
  <div class="container">
    <h1>NDE Internal Management System</h1>
    <form method="post">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html> 
```

```python
# core/forms/login_form.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm 

class LoginForm(AuthenticationForm):
    employee_id = forms.CharField(label="Employee ID", required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Password", required=True)
```


**4.1.2 Logout (`core:logout`)**

- **View:** `core/views.py` - Handles the logout logic.
- **Template:** No specific template required (redirects to login).

```python
# core/views.py
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('core:login') 
```


**4.1.3 Dashboard (`core:dashboard`)**

- **Template:** `core/templates/dashboard.html`
- **View:** `core/views.py` - Retrieves data for the dashboard based on user role.

```html
<!-- core/templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
  <title>NDE Dashboard</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'core/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Welcome, {{ request.user.get_username }}!</h2>
    {% if user.is_superuser %}
      <!-- DG Dashboard Content -->
    {% elif user.is_staff %}
      <!-- Staff Dashboard Content -->
    {% elif user.groups.filter(name='Director').exists %}
      <!-- Director Dashboard Content -->
    {% endif %}
  </div>
</body>
</html>
```


#### 4.2 HR App

**4.2.1 Employee List (`hr:employee_list`)**

- **Template:** `hr/templates/employee_list.html`
- **View:** `hr/views.py` - Retrieves and filters employee data.
- **Form:**  (Optional) For search/filter functionality.

```html
<!-- hr/templates/employee_list.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Employee List</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'hr/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Employee List</h2>
    <!-- Search/Filter Form (Optional) -->
    <table>
      <thead>
        <tr>
          <th>Employee ID</th>
          <th>Name</th>
          <th>Department</th>
          <th>Role</th>
          <th>...</th>
        </tr>
      </thead>
      <tbody>
        {% for employee in employees %}
          <tr>
            <td>{{ employee.employee_id }}</td>
            <td>{{ employee.first_name }} {{ employee.last_name }}</td>
            <td>{{ employee.department }}</td>
            <td>{{ employee.role }}</td>
            <td>
              <a href="{% url 'hr:employee_detail' employee.id %}">View Details</a>
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</body>
</html>
```

**4.2.2 Employee Detail (`hr:employee_detail`)**

- **Template:** `hr/templates/employee_detail.html`
- **View:** `hr/views.py` - Retrieves specific employee data.
- **Form:** `hr/forms/employee_update_form.py` (for editing employee information)

```html
<!-- hr/templates/employee_detail.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Employee Details</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'hr/css/styles.css' %}"> 
</head>
<body>
  <div class="container">
    <h2>Employee Details</h2>
    <p><strong>Employee ID:</strong> {{ employee.employee_id }}</p>
    <p><strong>Name:</strong> {{ employee.first_name }} {{ employee.last_name }}</p>
    <p><strong>Department:</strong> {{ employee.department }}</p>
    <!-- ... other employee details ... -->
    {% if request.user.has_perm('hr.change_employee') %}
      <a href="{% url 'hr:employee_update' employee.id %}">Edit Employee</a>
    {% endif %}
  </div>
</body>
</html>
```

```python
# hr/forms/employee_update_form.py
from django import forms
from .models import Employee

class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'department', 'role', ...]
```


**4.2.3 Employee Create (`hr:employee_create`)**

- **Template:** `hr/templates/employee_form.html`
- **View:** `hr/views.py` - Handles the creation of new employee records.
- **Form:** `hr/forms/employee_create_form.py` 

```html
<!-- hr/templates/employee_form.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Create Employee</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'hr/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Create New Employee</h2>
    <form method="post">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit">Create Employee</button>
    </form>
  </div>
</body>
</html>
```

```python
# hr/forms/employee_create_form.py
from django import forms
from .models import Employee

class EmployeeCreateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'department', 'role', ...] 
```


**4.2.4 Employee Update (`hr:employee_update`)**

- **Template:** `hr/templates/employee_form.html` (same as create)
- **View:** `hr/views.py` - Handles the update of existing employee records.
- **Form:** `hr/forms/employee_update_form.py` 


**4.2.5 Assign Role (`hr:assign_role`)**

- **Template:** `hr/templates/assign_role.html`
- **View:** `hr/views.py` - Handles role assignment/update.
- **Form:** `hr/forms/assign_role_form.py`

```html
<!-- hr/templates/assign_role.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Assign Role</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'hr/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Assign Role to {{ employee.first_name }} {{ employee.last_name }}</h2>
    <form method="post">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit">Assign Role</button>
    </form>
  </div>
</body>
</html>
```

```python
# hr/forms/assign_role_form.py
from django import forms
from django.contrib.auth.models import Group

class AssignRoleForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Group.objects.all(), label="Select Role")
```


**4.2.6 Performance Management (`hr:performance`)**

- **Templates:** `hr/templates/performance_review_form.html`, `hr/templates/performance_dashboard.html` 
- **Views:** `hr/views.py` - Views for creating reviews, managing objectives, and displaying performance dashboards.
- **Forms:** `hr/forms/performance_review_form.py`

```python
# hr/forms/performance_review_form.py
from django import forms
from .models import PerformanceReview 

class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['employee', 'review_period', 'overall_rating', ...]
```


**4.2.7 Training Management (`hr:training`)**

- **Templates:** `hr/templates/training_program_form.html`, `hr/templates/training_enrollment_form.html`, `hr/templates/training_report.html`
- **Views:** `hr/views.py` - Views for managing programs, enrolling employees, and generating reports.
- **Forms:** `hr/forms/training_program_form.py`, `hr/forms/training_enrollment_form.py`

```python
# hr/forms/training_program_form.py
from django import forms
from .models import TrainingProgram

class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = ['name', 'description', 'start_date', 'end_date', ...] 
```


**4.2.8 Retirement Management (`hr:retirement`)**

- **Templates:** `hr/templates/retirement_request_form.html`, `hr/templates/retirement_document_view.html`
- **Views:** `hr/views.py` - Views for managing retirement requests, documents, and communication.
- **Forms:** `hr/forms/retirement_request_form.py`

```python
# hr/forms/retirement_request_form.py
from django import forms
from .models import RetirementRequest

class RetirementRequestForm(forms.ModelForm):
    class Meta:
        model = RetirementRequest
        fields = ['employee', 'retirement_date', 'reason', ...]
```


**4.2.9 HR Reporting (`hr:reports`)**

- **Templates:** `hr/templates/hr_report.html` (various reports)
- **Views:** `hr/views.py` - Views for generating HR reports (e.g., employee demographics, turnover rate).


#### 4.3 Programs & Projects App

**4.3.1 Program List (`programs:program_list`)**

- **Template:** `programs/templates/program_list.html`
- **View:** `programs/views.py` - Retrieves and filters program data.
- **Form:** (Optional) For search/filter functionality.

```html
<!-- programs/templates/program_list.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Program List</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'programs/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Program List</h2>
    <!-- Search/Filter Form (Optional) -->
    <table>
      <thead>
        <tr>
          <th>Program Name</th>
          <th>Department</th>
          <th>Start Date</th>
          <th>Status</th>
          <th>...</th>
        </tr>
      </thead>
      <tbody>
        {% for program in programs %}
          <tr>
            <td>{{ program.name }}</td>
            <td>{{ program.department }}</td>
            <td>{{ program.start_date }}</td>
            <td>{{ program.status }}</td>
            <td>
              <a href="{% url 'programs:program_detail' program.id %}">View Details</a>
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</body>
</html>
```


**4.3.2 Program Detail (`programs:program_detail`)**

- **Template:** `programs/templates/program_detail.html`
- **View:** `programs/views.py` - Retrieves specific program data.
- **Form:** `programs/forms/program_update_form.py` (for editing program information)

```html
<!-- programs/templates/program_detail.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Program Details</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'programs/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Program Details: {{ program.name }}</h2>
    <p><strong>Department:</strong> {{ program.department }}</p>
    <p><strong>Start Date:</strong> {{ program.start_date }}</p>
    <!-- ... other program details ... -->
    {% if request.user.has_perm('programs.change_program') %}
      <a href="{% url 'programs:program_update' program.id %}">Edit Program</a>
    {% endif %}
  </div>
</body>
</html>
```

```python
# programs/forms/program_update_form.py
from django import forms
from .models import Program

class ProgramUpdateForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'description', 'department', 'start_date', 'end_date', ...] 
```


**4.3.3 Program Create (`programs:program_create`)**

- **Template:** `programs/templates/program_form.html`
- **View:** `programs/views.py` - Handles the creation of new program records.
- **Form:** `programs/forms/program_create_form.py`

```html
<!-- programs/templates/program_form.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Create Program</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'programs/css/styles.css' %}">
</head>
<body>
  <div class="container">
    <h2>Create New Program</h2>
    <form method="post">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit">Create Program</button>
    </form>
  </div>
</body>
</html>
```

```python
# programs/forms/program_create_form.py
from django import forms
from .models import Program

class ProgramCreateForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'description', 'department', 'start_date', 'end_date', ...]
```


**4.3.4 Program Update (`programs:program_update`)**

- **Template:** `programs/templates/program_form.html` (same as create)
- **View:** `programs/views.py` - Handles the update of existing program records.
- **Form:** `programs/forms/program_update_form.py`


**4.3.5 Collaboration Management (`programs:collaboration`)**

- **Templates:** `programs/templates/collaboration_form.html`, `programs/templates/collaboration_list.html`
- **Views:** `programs/views.py` - Views for managing collaborations with external organizations.
- **Forms:** `programs/forms/collaboration_form.py`


**4.3.6 Workflow Management (`programs:workflow`)**

- **Templates:** (Various templates based on specific workflows) 
- **Views:** `programs/views.py` - Views for managing workflow steps and transitions.
- **Forms:** (Various forms based on specific workflows, e.g., budget request form).

**4.3.7 Program Reporting (`programs:reports`)**

- **Templates:** `programs/templates/program_report.html` (various reports)
- **Views:** `programs/views.py` - Views for generating program reports (e.g., progress reports, beneficiary data).


#### 4.4 Finance & Accounts App

**4.4.1 Finance Dashboard (`finance:dashboard`)**

- **Template:** `finance/templates/dashboard.html`
- **View:** `finance/views.py` - Retrieves and displays financial data.


**4.4.2 Budget Management (`finance:budget`)**

- **Templates:** `finance/templates/budget_form.html`, `finance/templates/budget_list.html`
- **Views:** `finance/views.py` - Views for creating, managing, and approving budgets.
- **Forms:** `finance/forms/budget_form.py`


**4.4.3 Expense Management (`finance:expense`)**

- **Templates:** `finance/templates/expense_form.html`, `finance/templates/expense_report.html`
- **Views:** `finance/views.py` - Views for recording, tracking, and reporting on expenses.
- **Forms:** `finance/forms/expense_form.py`


**4.4.4 Revenue Management (`finance:revenue`)**

- **Templates:** `finance/templates/revenue_form.html`, `finance/templates/revenue_report.html`
- **Views:** `finance/views.py` - Views for managing revenue streams and generating reports.
- **Forms:** `finance/forms/revenue_form.py`


**4.4.5 Asset Management (`finance:asset`)**

- **Templates:** `finance/templates/asset_form.html`, `finance/templates/asset_list.html`
- **Views:** `finance/views.py` - Views for managing assets and generating reports.
- **Forms:** `finance/forms/asset_form.py`


**4.4.6 Financial Reporting (`finance:reports`)**

- **Templates:** `finance/templates/financial_report.html` (various reports)
- **Views:** `finance/views.py` - Views for generating financial reports (e.g., balance sheet, income statement).



#### 4.5 Monitoring & Evaluation App

**4.5.1 Inspectorate Dashboard (`monitoring:dashboard`)**

- **Template:** `monitoring/templates/dashboard.html`
- **View:** `monitoring/views.py` - Retrieves and displays monitoring data.


**4.5.2 Inspection Management (`monitoring:inspection`)**

- **Templates:** `monitoring/templates/inspection_form.html`, `monitoring/templates/inspection_report.html`
- **Views:** `monitoring/views.py` - Views for creating, managing, and reporting on inspections.
- **Forms:** `monitoring/forms/inspection_form.py`


**4.5.3 Compliance Tracking (`monitoring:compliance`)**

- **Templates:** `monitoring/templates/compliance_report.html`, `monitoring/templates/compliance_dashboard.html`
- **Views:** `monitoring/views.py` - Views for tracking and reporting on program compliance.


**4.5.4 Program Verification (`monitoring:verification`)**

- **Templates:** `monitoring/templates/verification_form.html`, `monitoring/templates/verification_report.html`
- **Views:** `monitoring/views.py` - Views for managing program verification processes.
- **Forms:** `monitoring/forms/verification_form.py`


**4.5.5 Reporting (`monitoring:reports`)**

- **Templates:** `monitoring/templates/monitoring_report.html` (various reports)
- **Views:** `monitoring/views.py` - Views for generating monitoring and evaluation reports.




### 5. IT Admin Team Management

The IT Admin team will require access to manage the system's overall health and configuration.  Here are the key aspects of system management they should be able to handle:

**5.1 User Management:**

- **Create/Edit/Delete User Accounts:**  Manage employee accounts, roles, and permissions.
- **Reset Passwords:** Allow IT Admins to reset user passwords.
- **Manage User Groups:**  Create, edit, and delete user groups.

**5.2 System Configuration:**

- **System Settings:** Manage global system settings (e.g., email settings, default values, etc.).
- **Database Management:** Manage backups, restores, and database optimization.
- **Application Logging:** Monitor system logs for errors and debugging.
- **Server Monitoring:** Monitor server performance, resource utilization, and uptime.

**5.3 Application Management:**

- **Deploy Updates:**  Manage application updates and deployments.
- **Manage Modules:**  Enable/Disable application modules or features.
- **Control Access to Features:**  Manage access to different modules or parts of the system.


**5.4 Security:**

- **Audit Logs:** Review audit logs for security events and suspicious activity.
- **Access Control:** Manage access controls for sensitive data and features.
- **Security Policies:** Implement and manage security policies for the system.


**5.5 Reporting and Analytics:**

- **System Performance Reports:** Generate reports on system performance (e.g., user activity, resource usage).
- **Error Logs:** Analyze error logs to identify and address issues.


### 6. Dark Mode Implementation

To cater to user preference and potentially reduce eye strain, the system should include a dark mode theme.

**Implementation Considerations:**

- **CSS Variables:** Use CSS variables (custom properties) to define colors and styles for light and dark themes.
- **JavaScript Toggle:** Implement a JavaScript toggle to switch between themes.
- **Theme Persistence:** Store user theme preference in session or local storage to maintain consistency.
- **Image Optimization:** Provide alternative images for dark mode (if necessary).
- **Accessibility:** Ensure that the dark mode theme is accessible to users with visual impairments.

**Example CSS (Simplified):**

```css
:root {
  --primary-color: #ffffff;
  --secondary-color: #f0f0f0;
  --text-color: #333333;
  --background-color: #e9ecef;
}

.dark-mode {
  --primary-color: #000000;
  --secondary-color: #222222;
  --text-color: #ffffff;
  --background-color: #333333;
}
```

**JavaScript (Simplified):**

```javascript
const toggleDarkMode = () => {
  document.body.classList.toggle('dark-mode');
  // Update local storage or session storage
};
```


### 7. Conclusion

This design document provides a comprehensive blueprint for the NDE Internal Management System. It covers various aspects of the system, including app views, templates, forms, IT Admin management, and the inclusion of a dark mode feature. Further details and specific implementations can be fleshed out in individual component documentation and design documents. 

---


**Note:** This document provides a high-level design.  You will need to expand upon it with detailed database schema design, model definitions, specific view logic, and more granular UI component design. I hope this is helpful in your project.  Feel free to ask if you have any further questions or need clarifications. I'm happy to assist you further. 
