import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import csv
import time


with open('Case-4.csv', newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    next(reader, None)  # Skip the header
    for row in reader:
        if row['Loan_Type']=='Bridging Loan':
                
            # Start the browser
   

            username = "aahmad@novelluscapital.co.uk"
            password = "747982"
            url = f"https://{username}:{password}@uat.lendingdynamics.com/dashboard#/sign-in/"

            driver = webdriver.Edge()
            driver.get(url)

            driver.maximize_window()
            
          

    # Wait until the email input box is available
            wait = WebDriverWait(driver, 20)
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys("bakioye@novelluscapital.co.uk")
            email_input.send_keys(Keys.RETURN)

    # Wait for the page to load
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

    # Wait for the code input box
            code_input = wait.until(EC.presence_of_element_located((By.NAME, "code")))
            code_input.send_keys("747982")
            code_input.send_keys(Keys.RETURN)

    # Wait for the next page to load
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(3)
            
          


            url = "https://uat.lendingdynamics.com/#/user-management/client-individual-listing"

            driver.get(url)

            driver.maximize_window()
            #submit_button = wait.until(EC.element_to_be_clickable((By.ID, "el-id-8023-1911")))
            #submit_button.click()

         # Wait for the page to load
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 

#Borrower Start

            #Client Borrower

            # Click 'Add Borrower' button
            add_Client_Individual_button = wait.until(EC.element_to_be_clickable((By.ID, "client-borrower-listing-add-new-borrower")))
            add_Client_Individual_button.click()
            

            # Fill out "Client Borrower" section
            #case_owner_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "deal_create_edit_form_case_owner_id_select")))
            #case_owner_dropdown.click()
            #case_owner_option = wait.until(EC.visibility_of_element_located((By.XPATH, f"//li[text()='{row['Case_Owner']}']")))
            #case_owner_option.click()

            # Fill in the Client Borrower Details Section
            
            # Borrower Email details
                    
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-email")))
            case_name_input.send_keys(row['Borrower-Email'])
            
            # Borrower Phone details
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-phone")))
            case_name_input.send_keys(row['Borrower-Phone'])

            # Select Title details
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-title")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-title-0")))
            type_option.click()
            

            # First Name
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-first_name")))
            case_name_input.send_keys(row['First-Name'])

            # Middle Name
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-middle_name")))
            case_name_input.send_keys(row['Middle-Name'])

            # Last Name
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-last_name")))
            case_name_input.send_keys(row['Last-Name'])

            # Nationality
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-nationality")))
            case_name_input.send_keys(row['Nationality'])

            # Passport Number
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-passport_number")))
            case_name_input.send_keys(row['Passport-No'])

            # Marital Status                                                        
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-marital_status_id")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-marital-status-0")))
            type_option.click()

            # Date of Birth - Day                                                      
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-dob_day")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-dob-day-0")))
            type_option.click()

            # Date of Birth - Month                                                      
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-dob_month")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-dob-month-0")))
            type_option.click()

            # Date of Birth - Year
            #case_owner_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-dob_year")))
            #case_owner_dropdown.click()
            #case_owner_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-dob-year-50")))
            #case_owner_option.click()

            
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-dob_year")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-dob-year-50")))
            type_option.click()

            # Permanent right to Remain in the UK - (Boolean)                                                      
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-permanent_uk_resident")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-uk_permanent-1")))
            type_option.click()

            # Residency Status
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-permanent_uk_resident_details")))
            case_name_input.send_keys('LTR')

            #Address
            #House name/number
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-house_number")))
            case_name_input.send_keys('British Museum')
                                                                   
            #Street
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-street")))
            case_name_input.send_keys('Great Russell St')
            #Employment Details
                                                                   
            #Town
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-district")))
            case_name_input.send_keys('London')

            #City
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-city")))
            case_name_input.send_keys('London')


            #County
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-county")))                                                                   
            case_name_input.send_keys('Lambeth')

            #Country                                                    
            #type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-country")))
            #type_dropdown.click()
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-country-item")))
            case_name_input.click()
            
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-country")))
            case_name_input.send_keys('United Kingdom')
            currency_option = wait.until(EC.visibility_of_element_located((By.XPATH, f"//li[text()='United Kingdom']")))
            currency_option.click()

            #Postcode
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-postcode")))
            case_name_input.send_keys('')

            #Owned or rented                                                      
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-ownership_type_id")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-ownership_type_id-1")))
            type_option.click()
                                                                   
            #Time at this address Years                                                    
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-lived_for_years")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-lived_for_years-10")))
            type_option.click()

            #Time at this address Months                                                   
            type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-lived_for_months")))
            type_dropdown.click()
            type_option = wait.until(EC.visibility_of_element_located((By.ID, "create-update-borrower-lived_for_months-10")))
            type_option.click()
                                  
#Borrower End
#Employment Start
                                                                   
            #Employment status
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-employment_status")))
            case_name_input.send_keys('Employed')                                                                   

            #Name of employer / Business
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-employer_name")))
            case_name_input.send_keys('Satchi & Satchi')                                                                      

            #Nature of business
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-nature_of_business")))
            case_name_input.send_keys('Media')                                                                      

            #Job title
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-job_title")))
            case_name_input.send_keys('Technical Producer')                                                                      

            #Total gross income                                                                   
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-total_gross_income")))
            case_name_input.send_keys('800000')                                                                      
                                                                                                                     
                                                                   
            # Click submit button
            submit_button = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-submit-form")))
            driver.execute_script("arguments[0].scrollIntoView();", submit_button)
            submit_button.click()
            time.sleep(5)

            #Client Company
            
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            url = "https://uat.lendingdynamics.com/#/user-management/client-companies-listing"

            driver.get(url)

            driver.maximize_window()
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 


            #add_Client_Individual_button = wait.until(EC.element_to_be_clickable((By.ID, "breadcrumb-top-user-management-client-companies-listing")))
            #add_Client_Individual_button.click()
            #Client Company
 # Click 'Add Company' button
            add_Client_Individual_button = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-listing-add-new-company")))
            add_Client_Individual_button.click()
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")             
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-name")))
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 
            case_name_input.send_keys('Company_name')
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-email")))
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 
            case_name_input.send_keys('cn@abc.com')


            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-phone")))
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 
            case_name_input.send_keys('11111111')



            #Address
            #House name/number
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-house_number")))
            case_name_input.send_keys('British Museum')
                                                                   
            #Street
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-street")))
            case_name_input.send_keys('Great Russell St')
            #Employment Details
                                                                   
            #Town
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-district")))
            case_name_input.send_keys('London')

            #City
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-city")))
            case_name_input.send_keys('London')


            #County
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-county")))                                                                   
            case_name_input.send_keys('Lambeth')

            #Country                                                    
            #type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "create-update-borrower-country")))
            #type_dropdown.click()
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-country-item")))
            case_name_input.click()
            
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-country")))
            case_name_input.send_keys('United Kingdom')
            currency_option = wait.until(EC.visibility_of_element_located((By.XPATH, f"//li[text()='United Kingdom']")))
            currency_option.click()

            #Postcode
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-postcode")))
            case_name_input.send_keys('')

                  #City
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-landline")))
            case_name_input.send_keys('1221112555')


            #County
            case_name_input = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-mobile")))                                                                   
            case_name_input.send_keys('1221112555')
           #breadcrumb-top-user-management-client-companies-listing

            submit_button = wait.until(EC.element_to_be_clickable((By.ID, "user-management-client-company-create-update-submit-button")))
            driver.execute_script("arguments[0].scrollIntoView();", submit_button)
            submit_button.click()


            
            driver.quit()
        else :
            continue


            #url = f"https://uat.lendingdynamics.com/#/case-manager/deals-listing-requests"

input("Press Enter to close the browser...")
driver.quit()
print("Browser closed.")
