// AutoApply Frontend JavaScript

class AutoApplyApp {
    constructor() {
        this.currentJobInfo = null;
        this.uploadedFile = null;
        this.init();
    }

    init() {
        this.checkHealth();
        this.checkConfig();
        this.bindEvents();
        this.loadStats();
    }

    // Health and Configuration
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                document.getElementById('health-status').textContent = 'Online';
                document.getElementById('health-status').className = 'status-badge status-good';
            } else {
                document.getElementById('health-status').textContent = 'Offline';
                document.getElementById('health-status').className = 'status-badge status-bad';
            }
        } catch (error) {
            document.getElementById('health-status').textContent = 'Error';
            document.getElementById('health-status').className = 'status-badge status-bad';
        }
    }

    async checkConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            const configStatus = document.getElementById('config-status');
            const configChecks = document.getElementById('config-checks');
            
            if (!data.all_configured) {
                configStatus.style.display = 'block';
                configStatus.className = 'alert alert-warning';
                
                let checksHtml = '<div class="row">';
                Object.entries(data.checks).forEach(([key, value]) => {
                    const icon = value ? 'bi-check-circle text-success' : 'bi-x-circle text-danger';
                    const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    checksHtml += `
                        <div class="col-md-6">
                            <i class="bi ${icon}"></i> ${label}
                        </div>
                    `;
                });
                checksHtml += '</div>';
                configChecks.innerHTML = checksHtml;
            }
        } catch (error) {
            console.error('Error checking configuration:', error);
        }
    }

    // Event Bindings
    bindEvents() {
        // Single Job Events
        document.getElementById('parse-btn').addEventListener('click', () => this.parseJobText());
        document.getElementById('apply-btn').addEventListener('click', () => this.applyToJob());
        document.getElementById('job-text').addEventListener('input', () => this.updateSteps());

        // Batch Processing Events
        document.getElementById('batch-file').addEventListener('change', () => this.handleFileSelection());
        document.getElementById('upload-btn').addEventListener('click', () => this.uploadFile());
        document.getElementById('process-btn').addEventListener('click', () => this.processBatchJobs());

        // Profile Events
        document.getElementById('save-profile-btn').addEventListener('click', () => this.saveProfile());
        document.getElementById('load-profile-btn').addEventListener('click', () => this.loadProfile());

        // Tab Events
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                if (e.target.id === 'stats-tab') {
                    this.loadStats();
                } else if (e.target.id === 'profile-tab') {
                    this.loadProfile();
                }
            });
        });
    }

    // Single Job Processing
    updateSteps() {
        const jobText = document.getElementById('job-text').value.trim();
        const step1 = document.getElementById('step-1');
        
        if (jobText) {
            step1.classList.add('completed');
        } else {
            step1.classList.remove('completed');
            this.resetSteps(2);
        }
    }

    resetSteps(fromStep = 1) {
        for (let i = fromStep; i <= 4; i++) {
            const step = document.getElementById(`step-${i}`);
            step.classList.remove('completed', 'active');
        }
    }

    async parseJobText() {
        const jobText = document.getElementById('job-text').value.trim();
        
        if (!jobText) {
            this.showError('Please paste a job description first.');
            return;
        }

        this.hideAlerts();
        this.showLoading('parse-loading');
        
        const step2 = document.getElementById('step-2');
        step2.classList.add('active');

        try {
            const response = await fetch('/api/job/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_text: jobText })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentJobInfo = data.job_info;
                this.displayJobInfo(data.job_info);
                
                step2.classList.remove('active');
                step2.classList.add('completed');
                
                document.getElementById('apply-btn').disabled = false;
            } else {
                throw new Error(data.error || 'Failed to parse job text');
            }
        } catch (error) {
            this.showError(`Error parsing job: ${error.message}`);
            step2.classList.remove('active');
        } finally {
            this.hideLoading('parse-loading');
        }
    }

    async applyToJob() {
        if (!this.currentJobInfo) {
            this.showError('Please parse job information first.');
            return;
        }

        this.hideAlerts();
        this.showLoading('apply-loading');
        
        const step3 = document.getElementById('step-3');
        step3.classList.add('active');

        try {
            const response = await fetch('/api/job/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_info: this.currentJobInfo })
            });

            const data = await response.json();

            if (response.ok && data.result.status === 'success') {
                this.displaySuccess(data.result);
                
                step3.classList.remove('active');
                step3.classList.add('completed');
                
                const step4 = document.getElementById('step-4');
                step4.classList.add('completed');
            } else {
                throw new Error(data.result?.error || data.error || 'Failed to generate documents');
            }
        } catch (error) {
            this.showError(`Error applying to job: ${error.message}`);
            step3.classList.remove('active');
        } finally {
            this.hideLoading('apply-loading');
        }
    }

    // Batch Processing
    handleFileSelection() {
        const fileInput = document.getElementById('batch-file');
        const uploadBtn = document.getElementById('upload-btn');
        
        if (fileInput.files.length > 0) {
            uploadBtn.disabled = false;
        } else {
            uploadBtn.disabled = true;
            document.getElementById('process-btn').disabled = true;
        }
    }

    async uploadFile() {
        const fileInput = document.getElementById('batch-file');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a file first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/batch/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.uploadedFile = data;
                document.getElementById('process-btn').disabled = false;
                this.showSuccess(`File uploaded: ${data.filename} (${data.format.toUpperCase()})`);
            } else {
                throw new Error(data.error || 'Failed to upload file');
            }
        } catch (error) {
            this.showError(`Error uploading file: ${error.message}`);
        }
    }

    async processBatchJobs() {
        if (!this.uploadedFile) {
            this.showError('Please upload a file first.');
            return;
        }

        this.hideAlerts();
        this.showLoading('batch-loading');

        try {
            const response = await fetch('/api/batch/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: this.uploadedFile.file_path,
                    format: this.uploadedFile.format
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayBatchResults(data.results);
            } else {
                throw new Error(data.error || 'Failed to process batch jobs');
            }
        } catch (error) {
            this.showError(`Error processing batch jobs: ${error.message}`);
        } finally {
            this.hideLoading('batch-loading');
        }
    }

    // Statistics
    async loadStats() {
        try {
            const [statsResponse, appsResponse] = await Promise.all([
                fetch('/api/stats'),
                fetch('/api/applications')
            ]);

            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                this.displayStats(statsData.stats);
            } else {
                document.getElementById('stats-content').innerHTML = 
                    '<p class="text-muted">Statistics unavailable. Check Google Sheets configuration.</p>';
            }

            if (appsResponse.ok) {
                const appsData = await appsResponse.json();
                this.displayRecentApps(appsData.applications);
            } else {
                document.getElementById('recent-apps').innerHTML = 
                    '<p class="text-muted">Recent applications unavailable.</p>';
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            document.getElementById('stats-content').innerHTML = 
                '<p class="text-danger">Error loading statistics.</p>';
            document.getElementById('recent-apps').innerHTML = 
                '<p class="text-danger">Error loading applications.</p>';
        }
    }

    // Display Functions
    displayJobInfo(jobInfo) {
        const jobInfoDiv = document.getElementById('job-info');
        const jobDetails = document.getElementById('job-details');
        
        const skillsList = jobInfo.required_skills ? jobInfo.required_skills.join(', ') : 'N/A';
        const description = jobInfo.description ? 
            (jobInfo.description.length > 200 ? 
                jobInfo.description.substring(0, 200) + '...' : 
                jobInfo.description) : 'N/A';

        jobDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>Position:</strong> ${jobInfo.position || 'N/A'}<br>
                    <strong>Company:</strong> ${jobInfo.company || 'N/A'}<br>
                    <strong>Location:</strong> ${jobInfo.location || 'N/A'}
                </div>
                <div class="col-md-6">
                    <strong>Remote:</strong> ${jobInfo.remote_ok || 'N/A'}<br>
                    <strong>Salary:</strong> ${jobInfo.salary_range || 'N/A'}<br>
                    <strong>Skills:</strong> ${skillsList}
                </div>
            </div>
            <div class="mt-2">
                <strong>Description:</strong><br>
                <small class="text-muted">${description}</small>
            </div>
        `;
        
        jobInfoDiv.style.display = 'block';
    }

    displaySuccess(result) {
        const successAlert = document.getElementById('success-alert');
        const successDetails = document.getElementById('success-details');
        
        successDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>Company:</strong> ${result.company}<br>
                    <strong>Position:</strong> ${result.position}<br>
                    <strong>Processing Time:</strong> ${result.processing_time.toFixed(2)}s
                </div>
                <div class="col-md-6">
                    <strong>Resume Generated:</strong> ✅<br>
                    <strong>Cover Letter Generated:</strong> ✅<br>
                    <strong>Tracked in Sheets:</strong> ${result.sheets_recorded ? '✅' : '❌'}
                </div>
            </div>
        `;
        
        // Populate the LaTeX and cover letter text areas
        if (result.resume_latex) {
            document.getElementById('latex-output').value = result.resume_latex;
        }
        
        if (result.cover_letter_text) {
            document.getElementById('cover-letter-output').value = result.cover_letter_text;
        }
        
        // Update Google Sheets data
        if (result.sheets_data) {
            this.updateSheetsData(result.sheets_data);
        }
        
        successAlert.style.display = 'block';
    }

    displayBatchResults(results) {
        const batchResults = document.getElementById('batch-results');
        const batchDetails = document.getElementById('batch-details');
        
        const successRate = results.total_jobs > 0 ? 
            (results.successful / results.total_jobs * 100).toFixed(1) : 0;

        batchDetails.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="text-center">
                        <h4 class="text-primary">${results.total_jobs}</h4>
                        <small>Total Jobs</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center">
                        <h4 class="text-success">${results.successful}</h4>
                        <small>Successful</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center">
                        <h4 class="text-warning">${successRate}%</h4>
                        <small>Success Rate</small>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <p><strong>Processing Time:</strong> ${results.processing_time.toFixed(2)} seconds</p>
                <p><strong>Files Generated:</strong></p>
                <ul>
                    <li>Resumes: output/resumes/</li>
                    <li>Cover Letters: output/cover_letters/</li>
                    <li>Simplify Exports: output/simplify_export/</li>
                </ul>
            </div>
        `;
        
        batchResults.style.display = 'block';
    }

    displayStats(stats) {
        const statsContent = document.getElementById('stats-content');
        
        if (!stats) {
            statsContent.innerHTML = '<p class="text-muted">No statistics available.</p>';
            return;
        }

        statsContent.innerHTML = `
            <div class="row text-center">
                <div class="col-6 col-md-3">
                    <h4 class="text-primary">${stats.total_applications || 0}</h4>
                    <small>Total Applications</small>
                </div>
                <div class="col-6 col-md-3">
                    <h4 class="text-success">${stats.response_rate || 0}%</h4>
                    <small>Response Rate</small>
                </div>
                <div class="col-6 col-md-3">
                    <h4 class="text-info">${stats.recent_applications || 0}</h4>
                    <small>This Week</small>
                </div>
                <div class="col-6 col-md-3">
                    <h4 class="text-warning">${stats.interviews_scheduled || 0}</h4>
                    <small>Interviews</small>
                </div>
            </div>
        `;
    }

    displayRecentApps(applications) {
        const recentApps = document.getElementById('recent-apps');
        
        if (!applications || applications.length === 0) {
            recentApps.innerHTML = '<p class="text-muted">No recent applications found.</p>';
            return;
        }

        let appsHtml = '<div class="list-group list-group-flush">';
        applications.slice(0, 10).forEach(app => {
            const statusColor = this.getStatusColor(app.Status);
            appsHtml += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${app.Position}</h6>
                        <small class="text-muted">${app['Application Date']}</small>
                    </div>
                    <p class="mb-1">${app.Company}</p>
                    <small class="badge bg-${statusColor}">${app.Status}</small>
                </div>
            `;
        });
        appsHtml += '</div>';
        
        recentApps.innerHTML = appsHtml;
    }

    // Utility Functions
    getStatusColor(status) {
        const statusMap = {
            'Applied': 'primary',
            'Response': 'success',
            'Interview': 'warning',
            'Offer': 'success',
            'Rejected': 'danger',
            'Pending': 'secondary'
        };
        return statusMap[status] || 'secondary';
    }

    showError(message) {
        const errorAlert = document.getElementById('error-alert');
        const errorDetails = document.getElementById('error-details');
        
        errorDetails.textContent = message;
        errorAlert.style.display = 'block';
    }

    showSuccess(message) {
        // Create or update a success message for batch operations
        let successDiv = document.getElementById('batch-success-alert');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'batch-success-alert';
            successDiv.className = 'alert alert-success mt-3';
            document.querySelector('#batch .card-body').appendChild(successDiv);
        }
        
        successDiv.innerHTML = `<i class="bi bi-check-circle"></i> ${message}`;
        successDiv.style.display = 'block';
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 5000);
    }

    showLoading(elementId) {
        document.getElementById(elementId).style.display = 'block';
    }

    hideLoading(elementId) {
        document.getElementById(elementId).style.display = 'none';
    }

    hideAlerts() {
        document.getElementById('success-alert').style.display = 'none';
        document.getElementById('error-alert').style.display = 'none';
        
        const batchSuccess = document.getElementById('batch-success-alert');
        if (batchSuccess) {
            batchSuccess.style.display = 'none';
        }
    }

    updateSheetsData(sheetsData) {
        // Format data for tab-separated values (for easy paste into Google Sheets)
        const dataRow = [
            sheetsData.date,
            sheetsData.company,
            sheetsData.position,
            sheetsData.location,
            sheetsData.salary,
            sheetsData.remote,
            sheetsData.status,
            sheetsData.job_url,
            sheetsData.notes,
            sheetsData.skills_required,
            sheetsData.application_method
        ].join('\t');
        
        document.getElementById('sheets-data').value = dataRow;
        document.getElementById('sheets-data-section').style.display = 'block';
    }

    // Profile Management Methods
    async loadProfile() {
        try {
            const response = await fetch('/api/profile');
            const data = await response.json();
            
            if (response.ok && data.profile) {
                const profile = data.profile;
                document.getElementById('profile-name').value = profile.name || '';
                document.getElementById('profile-email').value = profile.email || '';
                document.getElementById('profile-phone').value = profile.phone || '';
                document.getElementById('profile-linkedin').value = profile.linkedin || '';
                document.getElementById('profile-role').value = profile.current_role || '';
                document.getElementById('profile-experience').value = profile.experience_years || 0;
                document.getElementById('profile-skills').value = Array.isArray(profile.skills) ? profile.skills.join(', ') : '';
                document.getElementById('profile-summary').value = profile.summary || '';
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    }

    async saveProfile() {
        try {
            const skills = document.getElementById('profile-skills').value;
            const skillsArray = skills ? skills.split(',').map(s => s.trim()).filter(s => s) : [];
            
            const profile = {
                name: document.getElementById('profile-name').value,
                email: document.getElementById('profile-email').value,
                phone: document.getElementById('profile-phone').value,
                linkedin: document.getElementById('profile-linkedin').value,
                current_role: document.getElementById('profile-role').value,
                experience_years: parseInt(document.getElementById('profile-experience').value) || 0,
                skills: skillsArray,
                summary: document.getElementById('profile-summary').value,
                achievements: [],
                preferred_locations: [],
                salary_range: ""
            };

            const response = await fetch('/api/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ profile })
            });

            const data = await response.json();

            if (response.ok) {
                this.showProfileSuccess('Profile saved successfully!');
            } else {
                throw new Error(data.error || 'Failed to save profile');
            }
        } catch (error) {
            this.showProfileError(`Error saving profile: ${error.message}`);
        }
    }

    showProfileSuccess(message) {
        // Create or update success message
        let successDiv = document.getElementById('profile-success-alert');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'profile-success-alert';
            successDiv.className = 'alert alert-success mt-3';
            document.querySelector('#profile .card-body').appendChild(successDiv);
        }
        
        successDiv.innerHTML = `<i class="bi bi-check-circle"></i> ${message}`;
        successDiv.style.display = 'block';
        
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }

    showProfileError(message) {
        // Create or update error message
        let errorDiv = document.getElementById('profile-error-alert');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'profile-error-alert';
            errorDiv.className = 'alert alert-danger mt-3';
            document.querySelector('#profile .card-body').appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${message}`;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Copy to clipboard function
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    element.select();
    element.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        
        // Show brief success feedback
        const button = element.parentElement.querySelector('button');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check"></i> Copied!';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-primary');
        }, 2000);
    } catch (err) {
        console.error('Failed to copy text: ', err);
    }
}

// Sample file download function
function downloadSample(format) {
    // Create a temporary link element and click it to trigger download
    const link = document.createElement('a');
    link.href = `/api/sample/${format}`;
    link.download = `sample_jobs.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.autoApplyApp = new AutoApplyApp();
});