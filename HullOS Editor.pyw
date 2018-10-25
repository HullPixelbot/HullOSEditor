import sys
import glob
import serial
import time
import random
from tkinter import *
from tkinter import messagebox

from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

class CodeEditor(object):
    '''
    Provides an editor for a StockItem
    The frame property gives the Tkinter frame
    that is used to display the editor
    '''

    def clear_output(self):
        self.output_Text.delete('0.0', END)
        self.root.update()

    def serial_port_names(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        return ports

    def set_status(self,status):
        self.status_label.config(text=status)
        self.root.update()

    def set_serial_status_state(self, status):
        if status:
            self.serial_button_frame["bg"] = "green"
        else:
            self.serial_button_frame["bg"] = "red"
        self.root.update()

    def read_line_from_serial(self,ser):
        result = ""
        while True:
            b=ser.read(size=1)
            if len(b)==0:
                # timeout
                return result
            c = chr(b[0])
            if c=='\n':
                return result
            result = result + c

    def get_pixelbot_version(self, serial_port):
        try:
            time.sleep(1)
            self.send_text('*iv\n', serial_port)
            response = self.read_line_from_serial(serial_port)
            if response.startswith('HullOS'):
                return response
            else:
                return None
        except (OSError, serial.SerialException):
            return None

    def open_connection(self,port_name):
        try:
            port = serial.Serial(port_name, 1200, timeout=1)
        except (OSError, serial.SerialException):
            return None
        return port

    
    def try_to_connect(self,port_name):
        if self.trying_to_connect:
            return

        self.trying_to_connect = True
        
        port = self.open_connection(port_name)

        if port == None:
            self.set_serial_status_state(False)
            self.trying_to_connect = False
            return False

        self.set_status('Found port: ' + port_name)
        
        version = self.get_pixelbot_version(port)
        
        if version != None :
            self.serial_port = port
            self.set_status('Serial port ' + port_name + ' connected to Hull Pixelbot ' + version)
            self.clear_output()
            self.set_serial_status_state(True)
            self.trying_to_connect = False
            return True

        self.set_serial_status_state(False)
        self.trying_to_connect = False
        return False
    
    def do_connect_serial(self):
        
        if self.serial_port != None:
            self.set_status('Serial port already connected')
            return
        
        self.set_status('Connecting..')

        if self.last_working_port != None:
            if self.try_to_connect(self.last_working_port):
                return

        port_names = self.serial_port_names()

        for port_name in port_names:
            if self.try_to_connect(port_name):
                # We found a port - remember it
                self.last_working_port = port_name
                self.force_disconnect = False
                return

        self.set_status('No Pixelbots found')

    def dump_string(self,title, string):
        print(title, string)
        print(title,end='')
        for ch in string:
            print(ord(ch),end='')
        print()

    def save_snapshot_code(self, code):
        # self.dump_string('snapshot:', code)
        self.code_copy = code.strip()

    def snapshot_code(self):
        code =  self.code_Text.get('1.0',END)
        self.save_snapshot_code(code)


    def code_has_been_edited(self):
        code =  self.code_Text.get('1.0',END).strip()
        if self.code_copy==code:
            return False
        # self.dump_string('copy', self.code_copy)
        # self.dump_string('edit', code)
        return True

    def check_for_edit(self):
        if self.code_has_been_edited():
            if messagebox.askokcancel("Program changed","Would you like to save it first?"):
                self.do_save_code()
        
    def do_save_code(self):
        self.set_status('Saving code')
        
        file_path = asksaveasfilename(filetypes =(("Text File", "*.txt"),("All Files","*.*")),title = "Choose a file.")        
        
        self.set_status('Save the code in: ' + file_path)

        code =  self.code_Text.get('1.0',END)

        try:
            # create a file object 
            with open(file_path,'w') as output_file:
                output_file.write(str(code+'\n'))
        except:
            self.set_status('Something went wrong writing the file')

    
    def do_load_code(self):
        self.set_status('Loadiing code')

        self.check_for_edit()

        file_path = askopenfilename(filetypes =(("Text File", "*.txt"),("All Files","*.*")),title = "Choose a file.")        
        
        try:
            with open(file_path,'r') as input_file:
                code = input_file.read()
                self.code_Text.delete('0.0', END)
                self.code_Text.insert('0.0',code)
                snapshot_code(code)
        except:
            self.set_status('Something went wrong reading the file')

    def send_text(self, text, serial_port):
        
        if serial_port == None:
            self.set_status('Serial port not connected')
            return
        
        return_text = new_numbers_lambda = map(lambda x : x if x != '\n' else '\r', text)

        byte_text = bytearray()
        byte_text.extend(map(ord,return_text))

        serial_port.write(byte_text)
        
        self.set_status('Sent to robot')

    def do_send_code(self):

        self.set_status('Sending code')
        
        code =  self.code_Text.get('1.0',END)

        self.send_text(code, self.serial_port)

    def do_run_program(self):
        self.send_text('*rs\n', self.serial_port)
        self.clear_output()

    def do_stop_program(self):
        self.send_text('*rh\n', self.serial_port)

    def do_disconnect_serial(self):
        
        self.set_status('Serial port disconnected')
        
        if self.serial_port == None:
            return

        self.serial_port.close()

        self.serial_port = None
        self.force_disconnect = True
        self.set_serial_status_state(False)

    def update_output_text(self):
        if self.serial_port != None:
            try:
                while self.serial_port.in_waiting > 0:
                    b = self.serial_port.read()
                    c = chr(b[0])
                    self.output_Text.insert(END,c)
                    self.output_Text.see(END)
            except:
                self.serial_port.close()
                self.serial_port = None
                self.set_status('Serial port disconnected')
                self.set_serial_status_state(False)
        

    def do_tick(self):
        
        if self.serial_port == None:
            if not self.force_disconnect:
                # Only try to reconnect if the user
                # hasn't forced a disconnection
                if self.last_working_port != None:
                    # We have been unplugged - try to reconnect
                    self.serial_port = self.open_connection(self.last_working_port)
                    if self.serial_port != None:
                        self.set_status('Serial port reconnected')
                        self.set_serial_status_state(True)
        
        if self.serial_port != None:
            try:
                while self.serial_port.in_waiting > 0:
                    b = self.serial_port.read()
                    c = chr(b[0])
                    self.output_Text.insert(END,c)
                    self.output_Text.see(END)
            except:
                self.serial_port.close()
                self.serial_port = None
                self.set_status('Serial port disconnected')
                self.set_serial_status_state(False)
                
        self.root.after(1000,self.do_tick)
        

    def setup_random_programs(self):
        self.random_programs = []
        self.random_programs.append('''# Coloured flashing
begin
forever
  red
  delay 5
  green
  delay 5
end''')

        self.random_programs.append('''# Alarm 
begin
forever
  sound 1000
  delay 5
  sound 2000
  delay 5
end''')


        self.random_programs.append('''# square dance 
begin
forever
  move 100
  turn 90
end''')

        self.random_programs.append('''# distance light 
begin
forever
  d = @distance
  if d < 100:
    red
    continue
  if d < 200:
    yellow
    continue
  green
end''')

        self.random_programs.append('''# robot coward 
begin
forever
  green
  d = @distance
  if d < 100:
    red
    move -100
end''')

        self.random_programs.append('''# turn and run 
begin
forever
  green
  d = @distance
  if d < 100:
    red
    turn 180
    move 100
end''')

        self.random_programs.append('''# avoid obstacles 
begin
forever
  green
  move
  d = @distance
  if d < 100:
    red
    turn 90
end''')

        self.random_programs.append('''# spin the bottle
begin
forever
  green
  if @distance < 100:
    a = @random*30
    a = a+360
    red
    turn a
end''')

        self.random_programs.append('''# theramin
begin
forever
  f=@distance*20
  f=f+1000
  sound f
end''')


    def set_program(self, code):
        self.check_for_edit()
        self.code_Text.delete('0.0', END)
        self.code_Text.insert('0.0',code)
        self.save_snapshot_code(code)
        
    def do_random_program(self):
        # self.set_program(self.random_programs[8])
        self.set_program(random.choice(self.random_programs))

    def clear_program(self):
        code = 'begin\n# your program goes here\nend'
        self.set_program(code)

    def do_new_program(self):
        self.clear_program()

    def __init__(self,root):
        '''
        Create an instance of the editor. root provides
        the Tkinter root frame for the editor
        '''

        self.root = root

        Grid.rowconfigure(self.root, 0, weight=1)
        Grid.columnconfigure(self.root, 0, weight=1)

        self.root.title("HullOS Editor Vsn 2.0 Rob Miles")

        self.serial_port = None
        self.last_working_port = None
        self.force_disconnect = False
        self.trying_to_connect = False

        # used to detect when to save
        self.code_copy = ""
        
        self.frame = Frame(root,borderwidth=5)
        Grid.rowconfigure(self.frame, 0, weight=1)
        Grid.columnconfigure(self.frame, 1, weight=1)
        self.frame.grid(row=0,column=0, padx=5, pady=5,sticky='nsew')
   
        code_label = Label(self.frame,text='Code:')
        code_label.grid(sticky=E+N+S+W, row=0, column=0, padx=5, pady=5)

        self.code_Text = Text(self.frame,font=("Courier New", 25),width=40, height=15)
        self.code_Text.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        edit_Scrollbar = Scrollbar(self.frame, command=self.code_Text.yview)
        edit_Scrollbar.grid(row=0, column=2, sticky='nsew')
        self.code_Text['yscrollcommand'] = edit_Scrollbar.set

        output_label = Label(self.frame,text='Output:')
        output_label.grid(sticky=E+N, row=1, column=0, padx=5, pady=5)

        self.output_Text = Text(self.frame, height=5)
        self.output_Text.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

        output_Scrollbar = Scrollbar(self.frame, command=self.output_Text.yview)
        output_Scrollbar.grid(row=1, column=2, sticky='nsew')
        self.output_Text['yscrollcommand'] = output_Scrollbar.set

        program_button_frame = Frame(self.frame)

        saveButton = Button(program_button_frame, text='Save Program', command=self.do_save_code)
        saveButton.grid(sticky='nsew', row=0, column=0, padx=5, pady=5)

        loadButton = Button(program_button_frame, text='Load Program', command=self.do_load_code)
        loadButton.grid(sticky='nsew', row=0, column=1, padx=5, pady=5)

        sendButton = Button(program_button_frame, text='Send Program', command=self.do_send_code)
        sendButton.grid(sticky='nsew', row=0, column=2, padx=5, pady=5)

        runProgramButton = Button(program_button_frame, text='Run Program', command=self.do_run_program)
        runProgramButton.grid(sticky='nsew', row=0, column=3, padx=5, pady=5)

        stopProgramButton = Button(program_button_frame, text='Stop Program', command=self.do_stop_program)
        stopProgramButton.grid(sticky='nsew', row=0, column=4, padx=5, pady=5)

        randomProgramButton = Button(program_button_frame, text='Random Program', command=self.do_random_program)
        randomProgramButton.grid(sticky='nsew', row=0, column=5, padx=5, pady=5)

        newProgramButton = Button(program_button_frame, text='Clear Program', command=self.do_new_program)
        newProgramButton.grid(sticky='nsew', row=0, column=6, padx=5, pady=5)

        program_button_frame.grid(row=2, column=0, padx=5, pady=5, columnspan=2)

        self.serial_button_frame = Frame(self.frame)

        connectSerialButton = Button(self.serial_button_frame, text='Connect Robot', command=self.do_connect_serial)
        connectSerialButton.pack(padx=5, pady=5, side=LEFT)
        
        disconnectSerialButton = Button(self.serial_button_frame, text='Disconnect Robot', command=self.do_disconnect_serial)
        disconnectSerialButton.pack(padx=5, pady=5, side=RIGHT)
        
        self.serial_button_frame.grid(row=3, column=0, padx=5, pady=5, columnspan=2,sticky='nsew')
        self.set_serial_status_state(False)

        self.status_label = Label(self.frame,text="Status")
        self.status_label.grid(row=5, column=0, columnspan=5,sticky='nsew')

        root.update()
        # now root.geometry() returns valid size/placement
        root.minsize(root.winfo_width(), root.winfo_height())        

        self.do_tick()

        self.clear_program()

        self.setup_random_programs()

        self.do_connect_serial()
        
root=Tk()
editor=CodeEditor(root)
root.mainloop()

