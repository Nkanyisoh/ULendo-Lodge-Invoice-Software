# PythonAnywhere Deployment Guide for Ulendo Invoice App

## Prerequisites
- PythonAnywhere account (free or paid)
- Your project files ready for upload

## Step 1: Sign Up for PythonAnywhere
1. Go to [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Click "Get started for free" or choose a paid plan
3. Create your account and verify your email

## Step 2: Access Your PythonAnywhere Dashboard
1. Log in to PythonAnywhere
2. You'll see your dashboard with various options

## Step 3: Upload Your Project Files
### Option A: Using the Web Interface
1. In your dashboard, click on "Files" tab
2. Navigate to `/home/yourusername/`
3. Create a new directory called `UlendoInvoiceApp`
4. Upload all your project files to this directory

### Option B: Using Git (Recommended)
1. In your dashboard, click on "Consoles" tab
2. Start a new Bash console
3. Run these commands:
```bash
cd /home/yourusername
git clone https://github.com/yourusername/UlendoInvoiceApp.git
# OR if you don't have a git repo, create the directory and upload files manually
mkdir UlendoInvoiceApp
cd UlendoInvoiceApp
```

## Step 4: Install Dependencies
1. In the Bash console, navigate to your project:
```bash
cd /home/yourusername/UlendoInvoiceApp
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Install additional system dependencies (if needed):
```bash
pip install gunicorn
```

## Step 5: Configure the Web App
1. In your dashboard, click on "Web" tab
2. Click "Add a new web app"
3. Choose your domain (free users get `yourusername.pythonanywhere.com`)
4. Select "Manual configuration" (not Django)
5. Choose Python version 3.9 or 3.10

## Step 6: Configure WSGI File
1. In the Web tab, click on the WSGI configuration file link
2. Replace the content with the content from `wsgi.py` in your project
3. **IMPORTANT**: Change `/home/yourusername/UlendoInvoiceApp` to match your actual username
4. Save the file

## Step 7: Set Up Static Files
1. In the Web tab, scroll down to "Static files"
2. Add these static file mappings:
   - URL: `/assets/` → Directory: `/home/yourusername/UlendoInvoiceApp/assets/`
   - URL: `/generated/` → Directory: `/home/yourusername/UlendoInvoiceApp/generated/`

## Step 8: Configure Environment Variables
1. In the Web tab, scroll down to "Environment variables"
2. Add any environment variables your app needs
3. For security, consider changing the secret key

## Step 9: Set Up Database (if needed)
1. If you're using the SQLite database, make sure the `invoices.db` file is uploaded
2. Ensure the web app has write permissions to the directory

## Step 10: Reload Your Web App
1. In the Web tab, click the green "Reload" button
2. Wait for the reload to complete

## Step 11: Test Your Application
1. Visit your web app URL: `https://yourusername.pythonanywhere.com`
2. Test the login functionality
3. Test file uploads and invoice generation

## Troubleshooting Common Issues

### Issue: Module not found errors
**Solution**: Make sure all dependencies are installed in your virtual environment

### Issue: Permission denied errors
**Solution**: Check file permissions and ensure the web app can read/write to necessary directories

### Issue: Static files not loading
**Solution**: Verify static file mappings in the Web tab configuration

### Issue: Database errors
**Solution**: Ensure the database file exists and has proper permissions

### Issue: PDF generation fails
**Solution**: Some PDF libraries may not work on PythonAnywhere. Consider using alternative libraries like `reportlab` (which you already have)

## Security Considerations
1. Change the default secret key in production
2. Use environment variables for sensitive information
3. Consider using HTTPS (available on paid plans)
4. Regularly update dependencies

## Performance Tips
1. Use the paid plans for better performance
2. Optimize database queries
3. Use caching where appropriate
4. Monitor your app's resource usage

## Support
- PythonAnywhere forums: [https://www.pythonanywhere.com/forums/](https://www.pythonanywhere.com/forums/)
- PythonAnywhere help: [https://help.pythonanywhere.com/](https://help.pythonanywhere.com/)

## Next Steps
After successful deployment:
1. Set up a custom domain (paid plans)
2. Configure SSL certificates
3. Set up monitoring and logging
4. Plan for scaling as your user base grows
