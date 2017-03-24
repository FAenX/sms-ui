import platform
import json
import urllib
import urllib2
import time
import sys
import os
import base64
import ctypes

try:
    import Tkinter 
    import tkMessageBox as msg
except ImportError:
    sys.exit('Runtime import error for Tkinter')

# --------------------- #
# Configuration options #
# --------------------- #
class Config:

	home=os.path.expanduser('~')
	creddir=os.path.join(home,'bulksmsui')
	if not os.path.exists(creddir):
		os.mkdir(creddir)
		
		#tried to hide this directory but it is still visible

		FILE_ATTRIBUTE_HIDDEN = 0x02
		ret = ctypes.windll.kernel32.SetFileAttributesW(creddir,
													FILE_ATTRIBUTE_HIDDEN)

	default_from = platform.node()
	credentials_file = os.path.join(creddir,'credentials.db')
	credentials_dict = {}

	app_debug = True

	contacts_file = os.path.join(creddir,'contacts.db')
	contacts_dict = {}

# ---------------- #
# Widget utilities #
# ---------------- #
class WindowUtil:

    @staticmethod
    def center(window):

        window.update_idletasks()
        size_x = window.winfo_width()
        size_y = window.winfo_height()

        screen_x = window.winfo_screenwidth()
        screen_y = window.winfo_screenheight()

        offset_x = (screen_x - size_x) / 2
        offset_y = (screen_y - size_y) / 2

        geometry = (size_x, size_y, offset_x, offset_y)

        window.geometry('%dx%d+%d+%d' % geometry)


# ------------- #
# Logging class #
# ------------- #
class Log:

    now = time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def info(msg):

        if not Config.app_debug:
            return

        sys.stdout.write('[%s]: %s\n' % (Log.now, msg.strip()))

    @staticmethod
    def fatal(msg):

        sys.stdout.write('[%s]: %s\n' % (Log.now, msg.strip()))
        sys.exit(1)
        

# ------------------- #
# Nexmo message class #
# ------------------- #
class Nexmo:

    def __init__(self, sms_from, sms_to, sms_txt):

        nexmo_data = urllib.urlencode({
            'api_key':      Config.credentials_dict['key'],
            'api_secret':   Config.credentials_dict['secret'],
            'from':         sms_from,
            'to':           sms_to,
            'text':         sms_txt,
            'type':         'unicode',
        })
        
        

        self.sms_to = sms_to
        self.nexmo_url = 'https://rest.nexmo.com/sms/json?%s' % nexmo_data
        
        
    
    @staticmethod
    def checkCreds(api_key,api_secret):
        test_data=urllib.urlencode({
            'api_key':      Config.credentials_dict['key'],
            'api_secret':   Config.credentials_dict['secret'],})
        
        testCredsUrl='https://rest.nexmo.com/sms/json?%s' % test_data
        
        response=json.loads(urllib2.urlopen(testCredsUrl).read())
        response=response['messages'][0]
        status=response['status']
       
        if status !=u'4':
            return True
        else:
            return False


    def send(self):
        
        if misc.internet_on():

            Log.info('Sending SMS to %s...' % self.sms_to)
            nexmo_response = json.loads(urllib2.urlopen(self.nexmo_url).read())
            return nexmo_response
        else:
            msg_err = 'You need to be connected to the internet'
            msg.showinfo(title='Error', message=msg_err)
            return
            
    
# -------------- #
# Widget actions #
# -------------- #
class Action:


    # CREDENTIALS
    @staticmethod
    def credentials_save(key, secret):

        Log.info('Credentials saving')
        Config.credentials_dict = {
            'key': key,
            'secret': secret
        }

        open(Config.credentials_file, 'w').write(base64.b64encode(
            json.dumps(Config.credentials_dict, indent=4)
        ))

    @staticmethod
    def credentials_load():

        Log.info('Credentials loading')
        try:
            Config.credentials_dict = json.loads(base64.b64decode(
                open(Config.credentials_file, 'r').read()
            ))
        except IOError:
            pass
    
    # SMS
    @staticmethod
    def sms_conf():

        Log.info('ConfWindow starting')
        conf = ConfWindow(app)
        conf.title("Configure")
        WindowUtil.center(conf)
        
    @staticmethod
    def contacts_save():

        Log.info("Contacts saving")
        open(Config.contacts_file, 'w').write(json.dumps(Config.contacts_dict, indent=4))
        
    @staticmethod
    def contacts_load():

        Log.info("Contacts loading")
        try:
            Config.contacts_dict = json.loads(open(Config.contacts_file, 'r').read())
        except IOError:
            pass

        app.contacts.delete(0, Tkinter.END)
        for name, phone in Config.contacts_dict.items():
                
            app.contacts.insert(Tkinter.END, name)

    @staticmethod
    def contacts_delete():

        selected = app.contacts.curselection()
        if not selected:
            return
        contact = app.contacts.get(selected)

        Log.info('Deleting contact %s' % contact)
        app.contacts.delete(selected)
        del Config.contacts_dict[contact]
            
        Action.contacts_save()
        Action.sms_clear()
        
    @staticmethod
    def contacts_edit():

        selected = app.contacts.curselection()
        if not selected:
            return
        contact = app.contacts.get(selected)

        num = Config.contacts_dict[contact]
        edit = ContactsEditWindow(contact, num, app)
        edit.title('Edit contact')
        
    @staticmethod
    def contacts_new():#--------------------------------------------------------------------------!!!!!!!!!!!!!!!!!
        Log.info('ConfWindow starting')
        conf = AddContact(app)
        conf.title("Add contact")
        WindowUtil.center(conf)
        
    @staticmethod
    def sms_clear():

        Log.info("SMS clearing")
        app.entry_from.delete(0, Tkinter.END)
        #app.entry_to.delete(0, Tkinter.END) # do i need a to entry ? i dont think so because I want to send message to everyone in the database
        app.entry_txt.delete(0.0, Tkinter.END)
        
    @staticmethod
    def sms_send():
        

        Log.info("SMS validating")

        msg_err = None
        
         # collect form data
        sms_from = app.entry_from.get()
        sms_txt = app.entry_txt.get(1.0, Tkinter.END).strip()
        sms_txt = sms_txt.encode('utf-8')
        Log.info(sms_txt)
        
        # validate form data
        if not sms_from:
            msg_err = 'SMS sender cannot be empty'
        
        elif not sms_txt:
            msg_err = 'SMS text cannot be empty'
            
            
        if msg_err:
            msg.showinfo(title='Error', message=msg_err)
            Log.info(msg_err)
            return
        
       
            
        contact_list = Config.contacts_dict.values()
        if misc.internet_on():
			if len(Config.credentials_dict) !=0:
				if Nexmo.checkCreds(Config.credentials_dict['key'],Config.credentials_dict['secret']):
				
					for i in contact_list:
						# try to send
						Log.info('Connecting to Nexmo service')
					   
						response = Nexmo(sms_from, i, sms_txt).send()                  
															
						if response['messages'][0]['status'] == '0':
							msg_ok = u'SMS sent to %s.\n' % response['messages'][0]['to']
							msg_ok += u'Account balance now %s' % response['messages'][0]['remaining-balance']
							Log.info("Success"+ msg_ok)
							
						else:
							msg_err = 'Server response:\n%s' % str(response)
							msg.showinfo(title="Sending SMS failed", message=msg_err)
				else:
					msg_err = 'The credentials provided are invalid'
					msg.showinfo(title='Credentials error', message=msg_err)
					return
			else:
				msg_err = 'You need to configure your Nexmo key and secret'
				msg.showinfo(title='Credentials error', message=msg_err)
				return
                    
        else:            
			msg_err = 'you must be connected to the internet'
			msg.showinfo(title="No internet connection", message=msg_err)
			return
                
            
class ContactsEditWindow(Tkinter.Toplevel):

    def __init__(self, name, num, master=None):
        Tkinter.Toplevel.__init__(self, master)
        self.name = name
        self.num = num
        self.widgets()

    def save(self):
        
        new_name = self.edit_name.get()
        new_num  = self.edit_num.get()
        Log.info('Saving edited contact %s as %s' % (new_name, new_num))

        del Config.contacts_dict[self.name]
        Config.contacts_dict[new_name] = new_num
        Action.contacts_save()
        Action.contacts_load()
        self.destroy()
        
    def widgets(self):

        # TOP FRAME
        lf_top = Tkinter.LabelFrame(self, text='Edit contact')
        lf_top.pack(side=Tkinter.TOP,)

        lbl_name = Tkinter.Label(lf_top, text='Name:')
        lbl_num  = Tkinter.Label(lf_top, text='Number:')

        edit_name = Tkinter.Entry(lf_top,width=50)
        edit_num  = Tkinter.Entry(lf_top,width=50)

        self.edit_name = edit_name
        self.edit_num = edit_num

        edit_name.insert(0, self.name)
        edit_num.insert(0, self.num)

        lbl_name.grid(row=0, column=0)
        edit_name.grid(row=0, column=1)

        lbl_num.grid(row=1, column=0)
        edit_num.grid(row=1, column=1)

        # BOTTOM FRAME
        frm_bottom = Tkinter.Frame(self)
        frm_bottom.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)

        btn_save = Tkinter.Button(frm_bottom, text='Save', command=self.save)
        btn_cancel = Tkinter.Button(frm_bottom, text='Cancel', command=self.destroy)

        btn_save.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
        btn_cancel.pack(side=Tkinter.RIGHT, fill=Tkinter.X, expand=True)

# -------------------- #
# Configuration Window #
# -------------------- #
class ConfWindow(Tkinter.Toplevel):

    def __init__(self, master=None):
        Tkinter.Toplevel.__init__(self, master)
        self.widgets()

        if Config.credentials_dict:
            
            self.input_key.set(Config.credentials_dict['key'])
            self.input_secret.set(Config.credentials_dict['secret'])

    def save(self):

        key = self.input_key.get()
        secret = self.input_secret.get()

        if not key or not secret:
            msg.showinfo(title='Error', message='Cannot accept empty key or secret')
            return

        Action.credentials_save(key, secret)
        self.destroy()
            
    def clear(self):

        Log.info('Clearing credentials form')
        self.input_key.set('')
        self.input_secret.set('')

        try:
            os.remove(Config.credentials_file)
            Config.credentials_dict = {}
        except: pass

    def widgets(self):

        input_key = Tkinter.StringVar()
        input_secret = Tkinter.StringVar()

        self.input_key = input_key
        self.input_secret = input_secret

        lf = Tkinter.LabelFrame(self, text="Nexmo configuration")
        lf.pack(side=Tkinter.TOP, padx=5, pady=5)

        lbl_key = Tkinter.Label(lf, text="Nexmo key:")
        lbl_secret = Tkinter.Label(lf, text="Nexmo secret:")

        entry_key = Tkinter.Entry(lf, textvariable=input_key, width=50)
        entry_secret = Tkinter.Entry(lf, textvariable=input_secret, width=50, show="*")

        lbl_key.grid(row=0, column=0, sticky=Tkinter.W)
        entry_key.grid(row=0, column=1)

        lbl_secret.grid(row=1, column=0, sticky=Tkinter.W)
        entry_secret.grid(row=1, column=1)

        # buttons
        lf2 = Tkinter.Frame(self)
        lf2.pack(fill=Tkinter.X, expand=True, padx=5, pady=5)
        btn_save = Tkinter.Button(lf2, text="Save", command=self.save)
        btn_clear = Tkinter.Button(lf2, text="Clear", command=self.clear)
        btn_close = Tkinter.Button(lf2, text="Close", command=self.destroy)

        btn_save.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
        btn_clear.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
        btn_close.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)



class AddContact(Tkinter.Toplevel):

    def __init__(self, master=None):
        Tkinter.Toplevel.__init__(self, master)
        self.widgets()       
            
            

    def save(self):

        name = self.input_name.get()
        number = self.input_number.get()
        
        

        if not name or not number:
            msg.showinfo(title='Error', message='Cannot accept empty contact informaiton')#######
            return
        
         # if this is an already known contact
        # we don't wanna save it again
        if number in Config.contacts_dict.values():
            Log.info('Number %s already exists. Not saving again.' % number)
            return
        
        # add contact to dict
        
        Config.contacts_dict[name] = number

        Action.contacts_save()
        Action.contacts_load()
        self.destroy()
            
    def clear(self):
        try:
            os.remove(Config.contacts_file)
            Config.contacts_dict = {}
        except: pass

    def widgets(self):

        input_name = Tkinter.StringVar()
        input_number = Tkinter.StringVar()

        self.input_name = input_name
        self.input_number = input_number

        lf = Tkinter.LabelFrame(self, text="Nexmo configuration")
        lf.pack(side=Tkinter.TOP, padx=5, pady=5)

        lbl_name = Tkinter.Label(lf, text="Name:")
        lbl_number = Tkinter.Label(lf, text="Number:")

        entry_name = Tkinter.Entry(lf, textvariable=input_name, width=50)
        entry_number = Tkinter.Entry(lf, textvariable=input_number, width=50)

        lbl_name.grid(row=0, column=0, sticky=Tkinter.W)
        entry_name.grid(row=0, column=1)

        lbl_number.grid(row=1, column=0, sticky=Tkinter.W)
        entry_number.grid(row=1, column=1)

        # buttons
        lf2 = Tkinter.Frame(self)
        lf2.pack(fill=Tkinter.X, expand=True, padx=5, pady=5)
        btn_save = Tkinter.Button(lf2, text="Save", command=self.save)
        btn_clear = Tkinter.Button(lf2, text="Clear", command=self.clear)
        btn_close = Tkinter.Button(lf2, text="Close", command=self.destroy)

        btn_save.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
        btn_clear.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
        btn_close.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=True)
        
class misc:
    
    @staticmethod
    def internet_on():
        try:
            urllib2.urlopen('http://216.58.192.142', timeout=1)
            return True
        except urllib2.URLError as err: 
            return False
        
    
                
    
    
class smsUI(Tkinter.Frame):
  
    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.pack()
        self.widgets()

        
        
    def widgets(self):

		# contacts: labelframe
		lf_contacts = Tkinter.LabelFrame(self, text="Contacts")
		lf_contacts.pack(side=Tkinter.LEFT, anchor=Tkinter.NW, padx=18, pady=10)

		# contacts: listbox
		contacts = Tkinter.Listbox(lf_contacts, height=15)
		self.contacts = contacts

		contacts.pack(side=Tkinter.TOP)
		contacts.bind('<<ListboxSelect>>')

		# contacts controls: labelframe !!!!!!!!!!!!!!!!!!!!!!!!!!!!! here !!!!
		#lf_concontrols=Tkinter.LabelFrame(self,text="Controls")
		#lf_concontrols.pack(side=Tkinter.LEFT, anchor=Tkinter.SW, padx=18, pady=10)

		# contacts: buttons
		btn_del = Tkinter.Button(lf_contacts,text="Delete",command=Action.contacts_delete)
		btn_del.pack(side=Tkinter.RIGHT, fill=Tkinter.BOTH, expand=1)

		btn_edit = Tkinter.Button(lf_contacts, text="Edit", command=Action.contacts_edit)
		btn_edit.pack(side=Tkinter.RIGHT, fill=Tkinter.BOTH, expand=1)

		 # sms: labelframe
		lf_sms = Tkinter.LabelFrame(self, text="SMS")
		lf_sms.pack(side=Tkinter.TOP, anchor=Tkinter.NW, fill=Tkinter.BOTH, expand=True, padx=10, pady=10)

		# sms: from
		lbl_from = Tkinter.Label(lf_sms, text="From:")
		lbl_from.grid(row=0, column=0, padx=10, pady=5, sticky=Tkinter.W)

		entry_from = Tkinter.Entry(lf_sms, width=35)
		entry_from.grid(row=0, column=1, padx=10, pady=5, sticky=Tkinter.W)

		#---------------------------change here-----------------
		entry_from.insert(0, Config.default_from)
		self.entry_from = entry_from



		# sms: text
		lbl_txt= Tkinter.Label(lf_sms, text="Text:")
		lbl_txt.grid(row=2, column=0, padx=10, pady=5, sticky=Tkinter.N)

		entry_txt = Tkinter.Text(lf_sms, width=30, height=10)
		entry_txt.grid(row=2, column=1, padx=10, pady=5)
		self.entry_txt = entry_txt

		# sms: buttons
		lf_controls = Tkinter.LabelFrame(self, text="Controls")
		lf_controls.pack(side=Tkinter.RIGHT, anchor=Tkinter.SW, fill=Tkinter.X, expand=True, padx=5, pady=5)

		btn_conf = Tkinter.Button(lf_controls, text="Configure", command=Action.sms_conf)
		btn_send = Tkinter.Button(lf_controls, text="Send", command=Action.sms_send)
		btn_clear = Tkinter.Button(lf_controls, text="Clear", command=Action.sms_clear)
		btn_quit = Tkinter.Button(lf_controls, text="Quit", command=root.quit)
		btn_add_contact = Tkinter.Button(lf_controls, text="Add Contacts", command=Action.contacts_new)

		btn_conf.pack(side=Tkinter.LEFT, fill=Tkinter.X, anchor=Tkinter.S, expand=True)
		btn_send.pack(side=Tkinter.LEFT, fill=Tkinter.X, anchor=Tkinter.S, expand=True)
		btn_clear.pack(side=Tkinter.LEFT, fill=Tkinter.X, anchor=Tkinter.S, expand=True)
		btn_quit.pack(side=Tkinter.LEFT, fill=Tkinter.X, anchor=Tkinter.S, expand=True)
		btn_add_contact.pack(side=Tkinter.LEFT, fill=Tkinter.X, anchor=Tkinter.S, expand=True)


      

       
        
       
        
        
        
# ---------- #
# Main stuff # 
# ---------- #
os.umask(077)
Log.info('BULK SMS UI starting')       


#init screen
root = Tkinter.Tk()
root.geometry("500x300+300+300")
root.resizable(False,False)
root.title('BULK SMS UI')

#root.overrideredirect(True)

#init smsUI
app = smsUI(root)


#init data
Action.contacts_load()
Action.credentials_load()


root.mainloop()
Log.info("BULK SMS UI exiting")


