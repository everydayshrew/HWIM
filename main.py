import sys, pygame, time, os, math, sqlite3
from pygame.locals import *

global FPSCLOCK, DISPLAY 												# Create Clock and Display Vars
global MAP_DB
SIZE = [1120, 435]
DISPLAY = pygame.display.set_mode(SIZE)									# Create Display
FPSCLOCK = pygame.time.Clock()											# Create Clock 
FPS = 60																# FPS amount.
pygame.init()															# Initilize Pygame
pygame.display.set_caption("Hyrule Warriors Interactive Map")			# Set Title
EXIT = False															# Exit program flag

################################################################################################################
################################################################################################################
################################################################################################################
# Plays a menu sound.  More efficent than calling multiple library components every time I need
# a sound effect.
def play_sound(sfx = "cursormove"):
	sound = pygame.mixer.Sound("assets\\"+sfx+".wav")
	sound.set_volume(pygame.mixer.music.get_volume()+0.1)
	pygame.mixer.Sound.play(sound)

# Draws a special text box that consists of multiple boxes (and reduces lines used)
def draw_sbox(pos):
	pygame.draw.rect(DISPLAY, (232,176,0), [pos[0], pos[1], pos[2], pos[3]], 5)
	pygame.draw.rect(DISPLAY, (185,125,0), [pos[0]-1, pos[1]-1, pos[2]+3, pos[3]+3], 1)
	pygame.draw.rect(DISPLAY, (0,0,0), [pos[0]-3, pos[1]-3, pos[2]+6, pos[3]+6], 2)
	pygame.draw.rect(DISPLAY, (255,255,255), [pos[0]+3, pos[1]+3, pos[2]-6, pos[3]-6], 1)
	pygame.draw.rect(DISPLAY, (0,0,0), [pos[0]+5, pos[1]+5, pos[2]-10, pos[3]-10], 2)
	pygame.draw.rect(DISPLAY, (255,255,255), [pos[0]+1, pos[1]+1, 4, 4])
	pygame.draw.rect(DISPLAY, (255,255,255), [pos[0]+pos[2]-5, pos[1]+1, 4, 4])
	pygame.draw.rect(DISPLAY, (255,255,255), [pos[0]+1, pos[1]+pos[3]-5, 4, 4])
	pygame.draw.rect(DISPLAY, (255,255,255), [pos[0]+pos[2]-5, pos[1]+pos[3]-5, 4, 4])

# Load a specific tile clicked on.  Play the animation too.
def load_tile(pos, is_muted = False, old_volume = 1050):
	# Local Variables
	mouse_x = 0
	mouse_y = 0
	EXIT = False
	mouse_held = False
	mouse_event = False
	volume_hitbox = pygame.Rect([1020,395,100,40])	# Hitbox for the volume knob.

	# Letters dictate it's X position, numbers dictate it's Y position.
	# Converts the x/y position in the alphanumeric codes for each section of map
	x = chr(65 + (pos[0]/70))
	y = str(int(1+math.floor(pos[1]/48.125)))
	segment = y+x
	
	# Pull the segment filename and animate it.
	path_main = "assets\\{}\\".format(MAP_DB)
	path_tile = path_main+"map_segments"+"\\"+segment+".gif"
	try:			# Try to load it, if it doesn't exist, quit out of animation.
		image = pygame.image.load(path_tile)
	except pygame.error:
		return

	play_sound("zoomin")
	image = image.convert()
	for i in range(1,31):
		ratio = i / 30.0
		x = 70 + int(516*ratio)
		y = 42 + int(343*ratio)

		# Move the lefthand quarter towards the center from it's position on the field.
		x_pos = int((i/30.0)*207) + int(((30-i)/30.0)*pos[0])
		y_pos = int(((30-i)/30.0)*pos[1])
		
		# Every 5th frame, redraw the segment to prevent loss of quality.
		if i%5 == 0 or i == 1:
			image = pygame.image.load(path_tile).convert()
			background = pygame.image.load(path_main+'overworld.png').convert()
			DISPLAY.fill((0,0,0))
			background.set_alpha(50)
			DISPLAY.blit(background, [0,0,0,0])
			
		image = pygame.transform.scale(image, (x,y))
		DISPLAY.blit(image, [x_pos,y_pos,1000,1000])
		pygame.display.update()
		FPSCLOCK.tick(FPS)

	# Draw the info boxes
	draw_sbox([15, 10, 180, 150])
	draw_sbox([15, 175, 180, 80])
	draw_sbox([15, 275, 180, 100])
	draw_sbox([805, 10, 300, 375])
	adv_menu_box(1)

	# Draw the info
	load_info(segment)

	adv_vol_box((pygame.mixer.music.get_volume()*100)+1030)

	while not EXIT:
		#Event Handling
		for event in pygame.event.get():
			if event.type == QUIT:								# Exit (X button)
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN and event.key == K_ESCAPE or event.type == MOUSEBUTTONUP and event.button == 3:	# Back to Main Map (Escape)
				play_sound("zoomout")
				EXIT = True
			if event.type == MOUSEBUTTONUP:				# Mouse click/location Event
				mouse_x, mouse_y = event.pos
				#print mouse_x, mouse_y
				mouse_event = True
				mouse_held = False
			if event.type == MOUSEBUTTONDOWN:
				mouse_held = True
			if mouse_held and volume_hitbox.collidepoint(pygame.mouse.get_pos()):
				adjust_volume(pygame.mouse.get_pos()[0])

		if mouse_event:
			if mouse_x >= 1000 and mouse_x <= 1020 and mouse_y > 395:
				is_muted = not is_muted
				if is_muted:
					old_volume = pygame.mixer.music.get_volume() * 100 + 1030
					adjust_volume(1030)
				else:
					adjust_volume(old_volume)

			mouse_event = False

		# Update and Purge Events
		pygame.display.update()
		FPSCLOCK.tick(FPS)
		pygame.event.pump() # Process event queue.

# Draws the grid for the map.
def draw_grid():
	# TEMPORARY IF STATEMENT.  REMOVE WHEN ALL MAPS ARE AVAILABLE!
	if MAP_DB != "majora":
		for i in range (1,16):
			pygame.draw.line(DISPLAY, (0,0,0), (i*70,0), (i*70,385), 2)
		for i in range (1,8):
			pygame.draw.line(DISPLAY, (0,0,0), (0,i*48), (1120,i*48), 2)

# Pull from the database what items are given in victory conditions and draw them to the grid.
def load_info(segment):
	# Grab the font.
	font = pygame.font.Font("assets\ReturnofGanon.ttf", 20)
	DISPLAY.blit(font.render("A-Rank Requirements", 1, (255,255,0)), [35,20,150,150])
	
	path = "assets\\tile_data.db"
	with sqlite3.connect(path) as connection:
		c = connection.cursor()
		c.execute("SELECT * FROM "+MAP_DB+" WHERE LOC LIKE (?)", (segment,))
		for row in c.fetchall():
			#print row																# DEBUG DEBUG

			# Temp variables to fill out a rank information easily.
			a,b,c = "N/A","N/A","N/A"
			if row[1]!="0": a=row[1]
			if row[2]!="0": b=row[2]
			if row[3]!="0": c=row[3]

			# Draw 'A' Rank Requirements
			DISPLAY.blit(font.render("KOs:", 1, (255,255,0)), [30,60,150,150])
			DISPLAY.blit(font.render("Time:", 1, (255,255,0)), [30,90,150,150])
			DISPLAY.blit(font.render("Damage:", 1, (255,255,0)), [30,120,150,150])

			DISPLAY.blit(font.render(a, 1, (255,255,0)), [140,60,150,150])
			DISPLAY.blit(font.render(b, 1, (255,255,0)), [140,90,150,150])
			DISPLAY.blit(font.render(c, 1, (255,255,0)), [140,120,150,150])

			if row[4]: 											#Show off the Secret Region (if it exists)
				if row[4] != "Unknown":
					if len(row[4]) > 3:
						xpos = int(row[4][0:2]) - 1
						ypos = int(row[4][2:4]) - 1
					elif len(row[4]) > 2:
						xpos = int(row[4][0:2]) - 1
						ypos = int(row[4][2]) - 1
					else:
						xpos = int(row[4][0]) - 1
						ypos = int(row[4][1]) - 1

					# Highlight the square the secret is located.
					# Due to the map tiles of normal/master has 10.5 blocks (in y)
					# and the twilight/majora's mask has 11, the calculation must be adjusted
					# accordingly.  Remember kids, do your math.  DO IT.  DO THE MATHS.
					offset = 0
					if MAP_DB != "twilight":
						pygame.draw.rect(DISPLAY, (0,255,0), [205+int(xpos*36.62),int(ypos*36.6),40,38], 3)
					else:
						pygame.draw.rect(DISPLAY, (0,255,0), [205+int(xpos*36.62),int(ypos*35.15),40,38], 3)

					# Display the icon of the item needed next to the square.
					icon_image = pygame.image.load(os.path.join('assets\icons', row[5]+'.png')).convert_alpha()
					icon_image = pygame.transform.scale(icon_image, (36,36))
					n = 0			# Adjust the location of the icon depending on it's position on the grid.
					if xpos==16: n=-1 
					else: n=1
					DISPLAY.blit(icon_image,  [205+int((xpos+n)*36.62),int(ypos*35),40,38])
				else:
					pygame.draw.rect(DISPLAY, (0,0,0), [350,100,300,50])
					draw_sbox([355,105,290,42])
					DISPLAY.blit(font.render("Item Location Not Found Yet!", 1, (255,255,0)), [400,118,150,150])

			# Condition.  Find the center of the text box and place it's local position so it's always centered in the box.
			DISPLAY.blit(font.render("Conditions", 1, (255,255,0)), [72,182,150,150])
			d_text = font.render(row[6], 1, (255,255,0))
			DISPLAY.blit(d_text, [55+(50-d_text.get_rect()[2]/2),220,150,150])

			# Item Card (if any)
			DISPLAY.blit(font.render("Item Card", 1, (255,255,0)), [75,280,150,150])
			if row[9] and row[9].find("[") == -1:
				icon_image = pygame.image.load(os.path.join('assets\icons', row[9]+'.png')).convert_alpha()
				icon_image = pygame.transform.scale(icon_image, (50,50))
				DISPLAY.blit(icon_image,  [82,312,150,150])
			else:
				DISPLAY.blit(font.render("None", 1, (255,255,0)), [88,325,150,150])
		
			# Also we judge the size between 1-3 as a text will always exceed 3, but the tuple (if it)
			# Exists, will not.  I/K are variables to adjust the Y position of the icons
			i,k = 0,0

			tile_data = return_image_set(row[7])								# Secret Reward
			if len(tile_data) > 1 and len(tile_data) < 4:
				item = pygame.image.load(os.path.join('assets\icons', tile_data[1])).convert_alpha()
				item = pygame.transform.scale(item, (50,50))
				DISPLAY.blit(item,  [825,25,150,150])

				item = pygame.image.load(os.path.join('assets\icons', tile_data[0])).convert_alpha()
				item = pygame.transform.scale(item, (45,45))
				DISPLAY.blit(item, [840,40+(i*70),150,150])

				if tile_data[2]:
					DISPLAY.blit(font.render(tile_data[2], 1, (255,255,0)), [890,55,150,150])
				else:
					DISPLAY.blit(font.render("Secret Reward", 1, (255,255,0)), [890,55,150,150])
				i = i + 1

			tile_data = return_image_set(row[8])								# 'A' RAnk
			if len(tile_data) > 1 and len(tile_data) < 4:
				item = pygame.image.load(os.path.join('assets\icons', tile_data[1])).convert_alpha()
				item = pygame.transform.scale(item, (50,50))
				DISPLAY.blit(item,  [825,25+(i*70),150,150])

				item = pygame.image.load(os.path.join('assets\icons', tile_data[0])).convert_alpha()
				item = pygame.transform.scale(item, (45,45))
				DISPLAY.blit(item, [840,40+(i*70),150,150])

				DISPLAY.blit(font.render("'A Rank' Reward", 1, (255,255,0)), [890,50+(i*70),150,150])
				i = i + 1

			for x in range(9,14):												# Items/Rewards
				if row[x]:
					tile_data = return_image_set(row[x])
					if len(tile_data) > 1 and len(tile_data) < 4:
						new_y = 25 + (i*75) + (k*50)
						item = pygame.image.load(os.path.join('assets\icons', tile_data[1])).convert_alpha()
						item = pygame.transform.scale(item, (35,35))
						DISPLAY.blit(item,  [825,new_y,150,150])
						if tile_data[0]:
							item = pygame.image.load(os.path.join('assets\icons', tile_data[0])).convert_alpha()
							item = pygame.transform.scale(item, (35,35))
							DISPLAY.blit(item,  [840,new_y+15,150,150])

						if len(tile_data[2]) > 30:
							DISPLAY.blit(font.render(str(tile_data[2][0:26]), 1, (255,255,0)), [880,new_y-0,150,150])
							DISPLAY.blit(font.render(str(tile_data[2][27:]), 1, (255,255,0)), [880,new_y+20,150,150])
						else:
							DISPLAY.blit(font.render(str(tile_data[2]), 1, (255,255,0)), [880,new_y+10,150,150])
						k = k + 1

			# Restricted to
			if row[14] and row[14].find("[") == -1:
				DISPLAY.blit(font.render("Limited to", 1, (255,255,0)), [40,400,200,42])
				icon_image = pygame.image.load(os.path.join('assets\icons', row[14]+'.png')).convert_alpha()
				icon_image = pygame.transform.scale(icon_image, (35,35))
				DISPLAY.blit(icon_image,  [110,393,150,150])
				if row[15]:
					try:
						icon_image = pygame.image.load(os.path.join('assets\icons', row[15]+'.png')).convert_alpha()
						icon_image = pygame.transform.scale(icon_image, (35,35))
						DISPLAY.blit(icon_image,  [137,393,150,150])
					except pygame.error:
						icon_image = pygame.image.load(os.path.join('assets\icons', 'weapon.png')).convert_alpha()
						icon_image = pygame.transform.scale(icon_image, (35,35))
						DISPLAY.blit(icon_image,  [137,393,150,150])
			else:
				DISPLAY.blit(font.render("No Restrictions", 1, (255,255,0)), [45,400,200,42])

			
			if row[16]:
				if row[17]:
					font = pygame.font.Font("assets\ReturnofGanon.ttf", 22)
				else:
					font = pygame.font.Font("assets\ReturnofGanon.ttf", 24)
				level_text = None
				# Get the location of the level text if it exists
				a =	row[16].find("[")
				b = row[16].find("]")
				if a!=-1 and b!=-1:
					level_text = row[16][a+1:b]
					blurb_text = row[16][:a-1] + row[16][b+1:]
				else:
					blurb_text = row[16]

				# Forumla for centering text in the box.  X is the length of the text, which
				# is added to the according to values to center the text given a specific size.
				blurb_textbox = font.render(blurb_text, 1, (255,255,0))
				x = (470 - blurb_textbox.get_rect()[2])/2 + 300	# 300 is the X position I want to center from.
				if row[17]:
					DISPLAY.blit(blurb_textbox, [x+170, 400, 230, 42])
					DISPLAY.blit(font.render("Master Quest Condition:", 1, (255,0,0)), [225,400,200,42])
					DISPLAY.blit(font.render(row[17], 1, (255,255,255)), [415,400,200,42])
				else:
					DISPLAY.blit(blurb_textbox, [x, 400, 200, 42])

				font = pygame.font.Font("assets\ReturnofGanon.ttf", 24)
				if level_text:
					DISPLAY.blit(font.render(level_text, 1, (255,255,255)), [900, 400, 200, 42])
			

			

# Returns the icon set and dialog for victory rewards for a specific tile.
def return_image_set(text):
	item = None
	char = None

	# Find Item (load images)
	if text.find("PHeart")!=-1: item = "PHeart.png"
	elif text.find("CHeart")!=-1: item = "CHeart.png"
	elif text.find("Skulltula")!=-1: item = "Skulltula.png"
	elif text.find("Weapon")!=-1: item = "Weapon.png"
	elif text.find("Unlock")!=-1: item = "Unlock.png"
	elif text.find("Costume")!=-1: item = "Costume.png"
	# Find Character (load images)
	if text.find("[Link]")!=-1: char = "Link.png"
	elif text.find("[Impa]")!=-1: char = "Impa.png"
	elif text.find("[Lana]")!=-1: char = "Lana.png"
	elif text.find("[Zelda]")!=-1: char = "Zelda.png"
	elif text.find("[Sheik]")!=-1: char = "Sheik.png"
	elif text.find("[Gannondorf]")!=-1: char = "Gannondorf.png"
	elif text.find("[Darunia]")!=-1: char = "Darunia.png"
	elif text.find("[Ruto]")!=-1: char = "Ruto.png"
	elif text.find("[Agitha]")!=-1: char = "Agitha.png"
	elif text.find("[Midna]")!=-1: char = "Midna.png"
	elif text.find("[Zant]")!=-1: char = "Zant.png"
	elif text.find("[Fi]")!=-1: char = "Fi.png"
	elif text.find("[Ghirahim]")!=-1: char = "Ghirahim.png"
	elif text.find("[Volga]")!=-1: char = "Volga.png"
	elif text.find("[Twili]")!=-1: char = "Twili.png"
	elif text.find("[Wizzro]")!=-1: char = "Wizzro.png"
	elif text.find("[Cia]")!=-1: char = "Cia.png"
	elif text.find("[Youngling]")!=-1: char = "Youngling.png"
	elif text.find("[Tingle]")!=-1: char = "Tingle.png"

	if char or item:
		i = 0									# Kill switch if the database is glitched
		while text.find("]") != -1: 
			text = text[text.find("]")+2:]
			if i>4: break 
			else: i = i+1
		text = str(text)
		text.replace("u'", "")
		return [char,item,text]
	else:
		return text 								# Return just text.

# Advanced menu for the bottom of the screen.  If x = 0, show the default search function, if 1, keep it blank for state-text.
# if 2, its a variant of 1 that doesn't have two hitboxes.
def adv_menu_box(x=0, char="Link", item="Weapon"):
	pygame.draw.rect(DISPLAY, (0,0,0), [0, 385, 1100, 50])
	adv_vol_box()
	font = pygame.font.Font("assets\ReturnofGanon.ttf", 20)

	# Default View
	if x==0: 
		DISPLAY.blit(font.render("?", 1, (255,255,255)), [900,400,1000,42])
		draw_sbox([884,390,42,42])
		draw_sbox([0,390,300,42])
		DISPLAY.blit(font.render("Show all tiles that have        for        ", 1, (255,255,0)), [15,400,1000,42])
		item = pygame.image.load(os.path.join('assets\icons', item+".png")).convert_alpha()
		item = pygame.transform.scale(item, (20,20))
		DISPLAY.blit(item,  [190,400,150,150])
		
		try:
			item = pygame.image.load(os.path.join('assets\icons', char+".png")).convert_alpha()
		except:
			item = pygame.image.load(os.path.join('assets\icons', "null.png")).convert_alpha()
		item = pygame.transform.scale(item, (35,35))
		DISPLAY.blit(item,  [245,393,150,150])
	# Focused View
	if x==1:
		draw_sbox([0,390,200,42])
		draw_sbox([210,390,760,42])
		pass
	# Default View v2
	if x==2:
		DISPLAY.blit(font.render("?", 1, (255,255,255)), [900,400,1000,42])
		draw_sbox([884,390,42,42])
		draw_sbox([0,390,300,42])
		DISPLAY.blit(font.render("Show all tiles that have        ", 1, (255,255,0)), [15,400,1000,42])

		item = pygame.image.load(os.path.join('assets\icons', item+".png")).convert_alpha()
		item = pygame.transform.scale(item, (20,20))
		DISPLAY.blit(item,  [190,400,150,150])

	if x==0 or x==2:
		draw_sbox([475,390,160,42])
		if MAP_DB == "normal": DISPLAY.blit(font.render("Adventure Map", 1, (255,255,0)), [505,400,1000,42])
		if MAP_DB == "master": DISPLAY.blit(font.render("Master Quest Map", 1, (255,255,0)), [492,400,1000,42])
		if MAP_DB == "twilight": DISPLAY.blit(font.render("Twilight Map", 1, (255,255,0)), [515,400,1000,42])
		if MAP_DB == "majora": DISPLAY.blit(font.render("Majora's Mask Map", 1, (255,255,0)), [490,400,1000,42])

# Option to use the help guide for helpful hints! :)
def adv_help_guide():
	font = pygame.font.Font("assets\ReturnofGanon.ttf", 20)
	EXIT = False

	for i in range(1,15):
		ratio = i / 15.0
		y = int(85 * ratio)

		pygame.draw.rect(DISPLAY, (0,0,0), [0, 385-y, 1200, int(85*ratio)])
		pygame.draw.rect(DISPLAY, (0,0,0), [0, 0, 1200, int(55*ratio)])
		pygame.display.update()
		FPSCLOCK.tick(FPS)

	pygame.draw.rect(DISPLAY, (0,0,0), [0, 300, 1200, 85])

	DISPLAY.blit(font.render("Version Notice:   Some tiles may have incorrect names at this point in time.", 1, (255,255,255)), [315,15,1000,42])
	DISPLAY.blit(font.render("Click on a Tile to Expand it.  Escape or Right Click to exit out of it.", 1, (255,255,0)), [350,330,1000,42])
	DISPLAY.blit(font.render("Code: Windslash    Spritework: Thanatos-   Data: HylianAngel    Special Thanks: Hyrule Warriors Subreddit and Tikara for Support", 1, (255,255,255)), [110,305,1000,42])
	DISPLAY.blit(font.render("Item Search", 1, (255,255,0)), [100,360,1000,42])
	DISPLAY.blit(font.render("Map Select", 1, (255,255,0)), [520,360,1000,42])
	DISPLAY.blit(font.render("Volume Control", 1, (255,255,0)), [1000,360,1000,42])

	while not EXIT:
		mouse_event = False
		for event in pygame.event.get():
			if event.type == QUIT:									# Exit (X button)
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN and event.key == K_ESCAPE or event.type == MOUSEBUTTONUP:		# Back to Main Map (Escape)
				EXIT = True
				return None
			if event.type == MOUSEBUTTONUP:							# Mouse click/location Event
				mouse_x, mouse_y = event.pos
				mouse_event = True

		pygame.display.update()
		FPSCLOCK.tick(FPS)

# Advanced map selection of the main menu
def adv_map_select():
	EXIT = False
	mouse_event = False
	font = pygame.font.Font("assets\ReturnofGanon.ttf", 20)

	# Draw the Menu bar
	pygame.draw.rect(DISPLAY, (0,0,0), [475, 200, 165, 185])
	draw_sbox([475,200,160,42])
	draw_sbox([475,246,160,42])
	draw_sbox([475,292,160,42])
	draw_sbox([475,338,160,42])
	DISPLAY.blit(font.render("Adventure Map", 1, (255,255,0)), [505,209,1000,42])
	DISPLAY.blit(font.render("Master Quest Map", 1, (255,255,0)), [492,255,1000,42])
	DISPLAY.blit(font.render("Twilight Map", 1, (255,255,0)), [515,301,1000,42])
	DISPLAY.blit(font.render("Majora's Mask Map", 1, (255,255,0)), [490,347,1000,42])

	while not EXIT:
		mouse_event = False
		for event in pygame.event.get():
			if event.type == QUIT:									# Exit (X button)
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN and event.key == K_ESCAPE:		# Back to Main Map (Escape)
				EXIT = True
				return None
			if event.type == MOUSEBUTTONUP:							# Mouse click/location Event
				mouse_x, mouse_y = event.pos
				mouse_event = True

		if mouse_event:
			if mouse_x >= 475 and mouse_x <= 635:															
				if mouse_y <= 250 and mouse_y >= 210:
					pygame.mixer.music.load("assets\\theme.mp3")
					pygame.mixer.music.play(-1)
					return "normal"
				if mouse_y <= 300 and mouse_y >= 255:
					pygame.mixer.music.load("assets\\theme2.mp3")
					pygame.mixer.music.play(-1)
					return "master"
				if mouse_y <= 345 and mouse_y >= 301:
					pygame.mixer.music.load("assets\\theme3.mp3")
					pygame.mixer.music.play(-1)
					return "twilight"
				if mouse_y <= 390 and mouse_y >= 346:
					pygame.mixer.music.stop()
					pygame.mixer.music.load("assets\\theme4.mp3")
					pygame.mixer.music.play(-1)
					return "majora"
			else:
				return MAP_DB

		pygame.display.update()
		FPSCLOCK.tick(FPS)

# Advanced item component of the main menu
def adv_item_box():
	EXIT = False
	mouse_event = False

	# Draw menu bar
	pygame.draw.rect(DISPLAY, (0,0,0), [50, 333, 325, 55])
	draw_sbox([50,335,50,50])
	draw_sbox([100,335,50,50])
	draw_sbox([155,335,50,50])
	draw_sbox([210,335,50,50])
	draw_sbox([265,335,50,50])
	draw_sbox([320,335,50,50])
	item = pygame.image.load(os.path.join('assets\icons', "Costume.png")).convert_alpha()
	item = pygame.transform.scale(item, (30,30))
	DISPLAY.blit(item,  [60,345,150,150])
	item = pygame.image.load(os.path.join('assets\icons', "Weapon.png")).convert_alpha()
	item = pygame.transform.scale(item, (30,30))
	DISPLAY.blit(item,  [110,345,150,150])
	item = pygame.image.load(os.path.join('assets\icons', "CHeart.png")).convert_alpha()
	item = pygame.transform.scale(item, (30,30))
	DISPLAY.blit(item,  [165,345,150,150])
	item = pygame.image.load(os.path.join('assets\icons', "Skulltula.png")).convert_alpha()
	item = pygame.transform.scale(item, (30,30))
	DISPLAY.blit(item,  [220,345,150,150])
	item = pygame.image.load(os.path.join('assets\icons', "Items.png")).convert_alpha()
	item = pygame.transform.scale(item, (30,30))
	DISPLAY.blit(item,  [275,345,150,150])
	item = pygame.image.load(os.path.join('assets\icons', "Unlock.png")).convert_alpha()
	item = pygame.transform.scale(item, (30,30))
	DISPLAY.blit(item,  [330,345,150,150])
	while not EXIT:
		mouse_event = False
		for event in pygame.event.get():
			if event.type == QUIT:								# Exit (X button)
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN and event.key == K_ESCAPE:	# Back to Main Map (Escape)
				EXIT = True
				return None
			if event.type == MOUSEBUTTONUP:				# Mouse click/location Event
				mouse_x, mouse_y = event.pos
				mouse_event = True

		if mouse_event:
			if mouse_y >= 345 and mouse_y <= 375:															
				if mouse_x >= 100 and mouse_x <= 164:												
					play_sound()
					return "Weapon"
				elif mouse_x >= 165 and mouse_x <= 219:													
					play_sound()
					return "CHeart"
				elif mouse_x >= 220 and mouse_x <= 274:													
					play_sound()
					return "Skulltula"
				elif mouse_x >= 275 and mouse_x <= 314:													
					play_sound()
					return "Items"
				elif mouse_x >= 315 and mouse_x <= 370:
					play_sound()
					return "Unlock"
				elif mouse_x >= 60 and mouse_x <= 95:
					play_sound()
					return "Costume"
				else:
					return None
			else:
				return None


		pygame.display.update()
		FPSCLOCK.tick(FPS)

# Advanced char component of the main menu
def adv_char_box():
	EXIT = False
	clicked_char = False
	char_hitbox = []
	char_list = ["Link", "Fi", "Impa", "Lana", "Sheik", "Zelda", "Midna", "Darunia", "Zant", "Gannondorf", "Ruto", "Ghirahim", "Agitha", "Volga", "Cia", "Wizzro", "Twili", "Youngling", "Tingle"]

	pygame.draw.rect(DISPLAY, (0,0,0), [180, 10, 165, 325])
	pygame.draw.rect(DISPLAY, (0,0,0), [235,335,50,50])
	for i in range(0,19):
		if i < 18:	
			char_hitbox.append(pygame.Rect([180+((i%3)*55),5+((i/3)*55),50,50]))						# Draw the first 18 characters.
			draw_sbox(char_hitbox[i])
			try:	
				item = pygame.image.load(os.path.join('assets\icons', char_list[i]+".png")).convert_alpha()
			except:
				item = pygame.image.load(os.path.join('assets\icons', "null.png")).convert_alpha()
			item = pygame.transform.scale(item, (50,50))
			DISPLAY.blit(item, char_hitbox[i])
		else:																							# Draw the 19th (who knows when).
			char_hitbox.append(pygame.Rect([235,335,50,50]))
			draw_sbox(char_hitbox[i])
			try:	
				item = pygame.image.load(os.path.join('assets\icons', char_list[i]+".png")).convert_alpha()
			except:
				item = pygame.image.load(os.path.join('assets\icons', "null.png")).convert_alpha()
			item = pygame.transform.scale(item, (50,50))
			DISPLAY.blit(item, char_hitbox[i])

	while not EXIT:
		mouse_event = False
		for event in pygame.event.get():
			if event.type == QUIT:								# Exit (X button)
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN and event.key == K_ESCAPE:	# Back to Main Map (Escape)
				EXIT = True
				return None
			if event.type == MOUSEBUTTONUP:						# Mouse click/location Event
				mouse_x, mouse_y = event.pos
				mouse_event = True

		if mouse_event:											# If they click, see if they hit a hitbox.
			for hitbox in char_hitbox:
				if hitbox.collidepoint(mouse_x, mouse_y):
					clicked_char = True
					play_sound()
					return char_list[char_hitbox.index(hitbox)]
			if not clicked_char:
				return None

		pygame.display.update()
		FPSCLOCK.tick(FPS)

# Volume control knob
def adv_vol_box(x = 1050):
	# Clear the previous bar.
	pygame.draw.rect(DISPLAY, (0,0,0), [1000, 400, 120, 30])
	pygame.draw.rect(DISPLAY, (232,176,0), [1005, 407, 5,10])
	pygame.draw.polygon(DISPLAY, (232,176,0), [[1005,412], [1015,402], [1015,422]])
	pygame.draw.rect(DISPLAY, (55,55,55), [1030, 410, 80, 5])
	pygame.draw.rect(DISPLAY, (232,176,0), [x, 400, 10, 25])
	if x < 1035:
		pygame.draw.line(DISPLAY, (255,0,0), (1005,400), (1015,425), 3)

# This function is called when the user is grabbing/clicking the volume area.  This will automatically
# redraw the area and push the volume bar to the correct location.
def adjust_volume(x):
	MIN_X = 1030	# Min volume location
	MAX_X = 1100	# Max volume location
	OFFSET = 15 	# Offset that still registers motion (so they don't have to be exact)
	new_x = x
	if x>=MIN_X-OFFSET and x<=MAX_X+OFFSET:
		if x <= MIN_X:
			new_x = MIN_X
		if x >= MAX_X:
			new_x = MAX_X

		adv_vol_box(new_x)
		volume = (new_x - 1030) / 100.0
		pygame.mixer.music.set_volume(volume)

# Draw the main screen after exiting a submenu.
def load_menu(x=0, char="Link", item="Weapon"):
	pygame.draw.rect(DISPLAY, (0,0,0), [0, 365, 1120, 40])
	path = "assets\\{}\\overworld.png".format(MAP_DB)
	DISPLAY.blit(pygame.image.load(path), [0,0,500,500])		# Redraw Map after Exit
	draw_sbox([0,390,1000,42])
	draw_grid()
	adv_menu_box(x, char, item)

# This function takes the adv_menu_bar values and queries the database of the correct locations, then
# puts marks on the overwall map that match the query.
def find_values(state, chars):
	path = "assets\\tile_data.db".format(MAP_DB)
	
	#### For Weapons
	if state == "Weapon":
		item = "%Weapon%"
		char = "%["+chars+"]%"
		segments = []
	
		# We return the string from index [3-5] because as the query returns a unicode value that doesn't like string
		# comparison, so we translate it on the fly and stick it in an array for the function to walk through later.
		with sqlite3.connect(path) as connection:
			c = connection.cursor()
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Secret LIKE (?) AND Secret LIKE (?)", (item,char))
			for row in c.fetchall():
				segments.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Ranked LIKE (?) AND Ranked LIKE (?)", (item,char))
			for row in c.fetchall():
				segments.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Victory LIKE (?) AND Victory LIKE (?)", (item,char))
			for row in c.fetchall():
				segments.append(str(row)[3:5])

		for segment in segments:
			x = 70 * (ord(segment[1]) - 65) + 13
			y = 48 * (int(segment[0])-1)
			item = pygame.image.load(os.path.join('assets\icons', "Weapon.png")).convert_alpha()
			item = pygame.transform.scale(item, (45,45))
			DISPLAY.blit(item,  [x,y,150,150])
	#### For Items
	if state == "Items":
		with sqlite3.connect(path) as connection:
			c = connection.cursor()
			c.execute("SELECT LOC,Victory FROM "+MAP_DB+" WHERE Victory NOT LIKE '%[%]%' AND NOT Victory == ''")
			for row in c.fetchall():
				segment = row[0]
				value = row[1]
				x = 70 * (ord(segment[1]) - 65) + 13
				y = 48 * (int(segment[0])-1) 
				#print row[0]
				item = pygame.image.load(os.path.join('assets\icons', value+".png")).convert_alpha()
				item = pygame.transform.scale(item, (45,45))
				DISPLAY.blit(item,  [x,y,150,150])
	#### For Heart Containers/Pieces
	if state == "CHeart":
		item = "%"+state+"%"
		char = "%"+chars+"%"
		segments_c = []
		segments_p = []			# P is the array of pieces of heart.  C is the array of the Complete hearts.  Just for easier handling.
		
		# We return the string from index [3-5] because as the query returns a unicode value that doesn't like string
		# comparison, so we translate it on the fly and stick it in an array for the function to walk through later.
		# I feel like there is a more elegant way to do a query of this type, but no research has turned up anything.
		with sqlite3.connect(path) as connection:
			c = connection.cursor()
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Secret LIKE (?) AND Secret LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_c.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Ranked LIKE (?) AND Ranked LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_c.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Victory LIKE (?) AND Victory LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_c.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_1 LIKE (?) AND Item_1 LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_c.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_2 LIKE (?) AND Item_2 LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_c.append(str(row)[3:5])

			# Search for the Pieces of Heart for Characters
			item = "%PHeart%"
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Secret LIKE (?) AND Secret LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_p.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Ranked LIKE (?) AND Ranked LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_p.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Victory LIKE (?) AND Victory LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_p.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_1 LIKE (?) AND Item_1 LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_p.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_2 LIKE (?) AND Item_2 LIKE (?)", (item,char))
			for row in c.fetchall():
				segments_p.append(str(row)[3:5])

		# Take each segment in the array returned and paste their icon onto the grid.
		for segment in segments_c:
			x = 70 * (ord(segment[1]) - 65) + 5
			y = 48 * (int(segment[0])-1) + 10
			item = pygame.image.load(os.path.join('assets\icons', "CHeart.png")).convert_alpha()
			item = pygame.transform.scale(item, (30,30))
			DISPLAY.blit(item,  [x,y,150,150])
		for segment in segments_p:
			x = 70 * (ord(segment[1]) - 65) + 35
			y = 48 * (int(segment[0])-1) + 10
			item = pygame.image.load(os.path.join('assets\icons', "PHeart.png")).convert_alpha()
			item = pygame.transform.scale(item, (30,30))
			DISPLAY.blit(item,  [x,y,150,150])	
	#### For Skulltula			
	if state == "Skulltula":
		with sqlite3.connect(path) as connection:
			c = connection.cursor()
			# If something exists in the first array, we put it in the excess array so it
			# Properly renders on the tileset. 
			segments = []
			excess = []

			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_1 LIKE '[Skulltula]%'")
			for row in c.fetchall():
				if find(segments, str(row)[3:5]):
					excess.append(str(row)[3:5])
				else:
					segments.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_2 LIKE '[Skulltula]%'")
			for row in c.fetchall():
				if find(segments, str(row)[3:5]):
					excess.append(str(row)[3:5])
				else:
					segments.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_3 LIKE '[Skulltula]%'")
			for row in c.fetchall():
				if find(segments, str(row)[3:5]):
					excess.append(str(row)[3:5])
				else:
					segments.append(str(row)[3:5])
			c.execute("SELECT LOC FROM "+MAP_DB+" WHERE Item_4 LIKE '[Skulltula]%'")
			for row in c.fetchall():
				if find(segments, str(row)[3:5]):
					excess.append(str(row)[3:5])
				else:
					segments.append(str(row)[3:5])

		# Take each segment in the array returned and paste their icon onto the grid.
		for segment in segments:
			x = 70 * (ord(segment[1]) - 65) + 5
			y = 48 * (int(segment[0])-1) + 10
			item = pygame.image.load(os.path.join('assets\icons', "Skulltula.png")).convert_alpha()
			item = pygame.transform.scale(item, (30,30))
			DISPLAY.blit(item,  [x,y,150,150])
		for segment in excess:
			x = 70 * (ord(segment[1]) - 65) + 35
			y = 48 * (int(segment[0])-1) + 10
			item = pygame.image.load(os.path.join('assets\icons', "Skulltula.png")).convert_alpha()
			item = pygame.transform.scale(item, (30,30))
			DISPLAY.blit(item,  [x,y,150,150])

	##### For Unlocking Characters
	if state == "Unlock":
		with sqlite3.connect(path) as connection:
			c = connection.cursor()
			c.execute("SELECT LOC,Secret FROM "+MAP_DB+" WHERE Secret LIKE '%Unlock%'")
			for row in c.fetchall():
				segment = row[0]
				value = str(row[1])[10:-1]				# Since unlock is uniform in the database, we'll just translate it on the fly.
				x = 70 * (ord(segment[1]) - 65) + 13
				y = 48 * (int(segment[0])-1) + 0
				item = pygame.image.load(os.path.join('assets\icons', value+".png")).convert_alpha()
				item = pygame.transform.scale(item, (50,50))
				DISPLAY.blit(item,  [x,y,150,150])

	##### For Unlocking Costumes
	if state == "Costume":
		with sqlite3.connect(path) as connection:
			c = connection.cursor()
			c.execute("SELECT LOC,Secret FROM "+MAP_DB+" WHERE Secret LIKE '%Costume%'")
			for row in c.fetchall():
				segment = row[0]
				value = str(row[1])[11:(row[1][11:-1].find("]"))+11]				# Costume is almost uniform.  We'll do quick math as the structure is [Costume] [Name] Description
				x = 70 * (ord(segment[1]) - 65) + 13 								# So we searcg for the second ending bracket and return the value inside. 11 to 11+index.
				y = 48 * (int(segment[0])-1) + 0
				item = pygame.image.load(os.path.join('assets\icons', value+".png")).convert_alpha()
				item = pygame.transform.scale(item, (50,50))
				DISPLAY.blit(item,  [x,y,150,150])

# Simple function to find if value exists in an array.  Returns true if it does.
def find(self, value):
	try:
		self.index(value)
		return True
	except ValueError:
		return False

################################################################################################################
################################################################################################################
################################################################################################################

# Local Variables
volume_bar = 1050
old_volume = 1050
mouse_event = False
mouse_x = 0 
mouse_y = 0
char = "Link"
item = "Weapon"
MAP_DB = "normal"
temp_var = None
adv_menu_state = 0 								# State of the adv_menu.
mouse_held = False								# State of mouse if being held down.
is_muted = False								# Is the sound muted?
volume_hitbox = pygame.Rect([1020,395,100,40])	# Hitbox for the volume knob.
path = "assets\\{}\\overworld.png".format(MAP_DB)

DISPLAY.blit(pygame.image.load(path), [0,0,500,500])
pygame.mixer.music.load("assets\\theme.mp3")
pygame.mixer.music.play(-1)
adjust_volume(volume_bar)
draw_grid()
adv_menu_box()

while not EXIT:
	mouse_event = False
	mouse_x = 0 
	mouse_y = 0

	for event in pygame.event.get():
		if event.type == QUIT:							# Exit (X button)
			pygame.quit()
			sys.exit()
		elif event.type == MOUSEBUTTONUP:				# Mouse click/location Event
			mouse_x, mouse_y = event.pos
			mouse_event = True
			mouse_held = False
			#print event.pos
		elif event.type == MOUSEBUTTONDOWN:
			mouse_x, mouse_y = event.pos
			mouse_held = True

	if mouse_event:
		if mouse_y < 385:																			# If they're clicking a tile, go here.\
			load_tile([mouse_x, mouse_y], is_muted, old_volume)
			load_menu(adv_menu_state, char, item)													# Reload the main menu / map.
			if pygame.mixer.music.get_volume() == 0:
				is_muted = True
				adjust_volume(1030)
			else:
				adjust_volume((pygame.mixer.music.get_volume()*100)+1030)
		elif mouse_y > 395:																			# If they're not, figure out if they're clicking the options our sound
			if mouse_x >= 190 and mouse_x <= 210:													# Approximate Hitbox of Item Knob
				play_sound()
				temp_var = adv_item_box()
				if temp_var:
					item = temp_var
					if item == "Skulltula" or item == "Items" or item == "Unlock" or item == "Costume":
						adv_menu_state = 2
					else: 
						adv_menu_state = 0
				load_menu(adv_menu_state, char, item)
				find_values(item,char)
				if pygame.mixer.music.get_volume() == 0:
					is_muted = True
					adjust_volume(1030)
				else:
					adjust_volume((pygame.mixer.music.get_volume()*100)+1030)
			if mouse_x >= 250 and mouse_x <= 275 and adv_menu_state != 2:							# Approximate Hitbox of Character Knob
				play_sound()
				temp_var = adv_char_box()
				if temp_var:
					char = temp_var
				load_menu(adv_menu_state, char, item)
				find_values(item,char)
			if mouse_x >= 1000 and mouse_x <= 1020:													# Approximate Hitbox of Volume Knob
				is_muted = not is_muted
				if is_muted:
					old_volume = pygame.mixer.music.get_volume() * 100 + 1030
					adjust_volume(1030)
				else:
					adjust_volume(old_volume)
			if mouse_x >= 470 and mouse_x <= 650:													# Approximate Hitbox of Map Select
				play_sound()
				MAP_DB = adv_map_select()
				load_menu(adv_menu_state, char, item)
				if pygame.mixer.music.get_volume() == 0:
					is_muted = True
					adjust_volume(1030)
				else:
					adjust_volume((pygame.mixer.music.get_volume()*100)+1030)
			if mouse_x >= 884 and mouse_x <= 926:
				play_sound()
				adv_help_guide()
				load_menu(adv_menu_state, char, item)
				if pygame.mixer.music.get_volume() == 0:
					is_muted = True
					adjust_volume(1030)
				else:
					adjust_volume((pygame.mixer.music.get_volume()*100)+1030)

	if mouse_held and volume_hitbox.collidepoint(pygame.mouse.get_pos()):
		is_muted = False
		adjust_volume(pygame.mouse.get_pos()[0])

	pygame.display.update()
	FPSCLOCK.tick(FPS)
	pygame.event.pump() # Process event queue.
