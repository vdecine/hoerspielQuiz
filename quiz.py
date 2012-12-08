import pygame
from pygame.locals import *
import pygame.movie
import os
import sys
import random
import eyeD3



fullscreen = False




# Class to handle a single episode
class Episode:

  def __init__(self, root, folder):
    self.root = root
    self.folder = folder
    self.cover = os.path.join(root, folder, 'cover.jpg')
    self.mediafiles = []
    self.scan()


  # Scans the gicen directory for mp3 files
  def scan(self):
    child_list = os.listdir(os.path.join(self.root, self.folder))
    for child in child_list:
      if child[len(child)-3:] == 'mp3':
        self.mediafiles.append(os.path.join(self.root, self.folder, child))


  # Return a random media file
  def getMedia(self):
    media = random.choice(self.mediafiles)
    header = eyeD3.Mp3AudioFile(media)
    duration = header.getPlayTime()
    startpos = 0
    if duration > 240:
      startpos = random.randint(120, duration - 120)
    return (media, startpos)




# Manages all episodes and generates quiz tasks
class TaskGen:

  def __init__(self, mp3folder):
    self.mp3folder = mp3folder
    self.episodes = []
    self.scan()


  # Scans the directory for episodes that have a cover file
  def scan(self):
    for root, folders, files in os.walk(self.mp3folder):
      for folder in folders:
        child_list = os.listdir(os.path.join(root, folder))
        if 'cover.jpg' in child_list:
          ep = Episode(root, folder)
          self.episodes.append(ep)


  # Generates a task (set of three epsiode's media files)
  def getTask(self):
    eps = random.sample(self.episodes, 3)
    return eps




# A simple time based on pygame's clock
class Timer:

  def __init__(self):
    self.clock = pygame.time.Clock()
    self.start_time = 0.0
    self.stop_time = 0.0
    self.running = False


  def start(self):
    self.start_time = pygame.time.get_ticks() / 1000.0
    self.running = True


  def stop(self):
    self.stop_time = pygame.time.get_ticks() / 1000.0
    self.elapsed_time = self.stop_time - self.start_time
    self.running = False


  def get_progress(self):
    if self.running:
      now = pygame.time.get_ticks() / 1000.0
      self.elapsed_time = now - self.start_time
    return self.elapsed_time




# Class to handle user scores
class Scoreboard:

  def __init__(self, user1, user2):
    self.user1 = user1
    self.user2 = user2
    self.scores = [0,0]
    self.active_user = -1


  def set_active_user(self, user):
    self.active_user = user


  def update_score(self, userbystatus, points):
    if userbystatus == 'active':
      self.scores[self.active_user] += points
    else:
      self.scores[abs(self.active_user - 1)] += points


  def get_score(self, user):
    return self.scores[user]


  def toggle_active(self):
    self.active_user = abs(self.active_user - 1)




# The main quiz, handling events and drawing of the interface
class Quiz:

  def __init__(self, user1, user2, episode_path):
    random.seed()
    self.running = True
    self.tasks = TaskGen(episode_path)
    self.score_board = Scoreboard(user1, user2)
    self.mode = 0
    self.answer = -1
    self.taskTimer = Timer()
    self.guessTimer = Timer()

    pygame.init()
    if fullscreen:
      self.screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
    else:
      self.screen = pygame.display.set_mode((1280, 720))
    self.clock = pygame.time.Clock()
    self.running = True
    self.back = pygame.image.load("images/back.jpg").convert()
    self.case1 = pygame.image.load("images/case.png").convert_alpha()
    self.case2 = pygame.image.load("images/case.png").convert_alpha()
    self.case3 = pygame.image.load("images/case.png").convert_alpha()
    self.active = pygame.image.load("images/guess1.png").convert_alpha()
    self.font = pygame.font.Font("Ubuntu.ttf", 25)
    self.fontTimer = pygame.font.Font("Ubuntu.ttf", 85)
    self.name1Label = self.font.render(self.score_board.user1, 1, (255,255,255))
    self.score1Label = self.font.render("0", 1, (255,255,255))
    self.name2Label = self.font.render(self.score_board.user2, 1, (255,255,255))
    self.score2Label = self.font.render("0", 1, (255,255,255))
    self.timerLabel = self.fontTimer.render("0", 1, (255,255,255))
    self.startTask()


  def startTask(self):
    episodes = self.tasks.getTask()

    self.cover1 = pygame.image.load(episodes[0].cover).convert()
    self.cover2 = pygame.image.load(episodes[1].cover).convert()
    self.cover3 = pygame.image.load(episodes[2].cover).convert()
    self.cover1 = pygame.transform.scale(self.cover1, (275, 275))
    self.cover2 = pygame.transform.scale(self.cover2, (275, 275))
    self.cover3 = pygame.transform.scale(self.cover3, (275, 275))
    self.case1 = pygame.image.load("images/case.png").convert_alpha()
    self.case2 = pygame.image.load("images/case.png").convert_alpha()
    self.case3 = pygame.image.load("images/case.png").convert_alpha()

    target = random.choice([0,1,2])
    self.answer = target
    mediafile, startpos = episodes[target].getMedia()
    pygame.mixer.music.load(mediafile)
    pygame.mixer.music.play(-1, startpos)
    self.taskTimer.start()


  # One user hit the buzzer
  def on_guess(self, user):

    # Prevent users from stealing answer after first buzz
    if self.mode == 1:
      return

    # Go into answer guess mode (first user)
    self.mode = 1

    # Stop music and update screen for answer mode
    pygame.mixer.music.stop()
    self.score_board.set_active_user(user)
    self.taskTimer.stop()
    self.case1 = pygame.image.load("images/case_1.png").convert_alpha()
    self.case2 = pygame.image.load("images/case_2.png").convert_alpha()
    self.case3 = pygame.image.load("images/case_3.png").convert_alpha()
    self.guessTimer.start()
    self.on_render()



  # Go into answer mode (one user hit the buzzer)
  def on_answer(self, answer):

    # Only accept answers in guess mode
    if self.mode != 1 and self.mode != 2:
      return

    # Go into answer mode
    self.mode = 3

    self.guessTimer.stop()

    # Depending on how fast the task was solved, player gets more points
    tasktime = self.taskTimer.get_progress()
    level = 1
    if tasktime < 20:
      level = 2
    if tasktime < 5:
      level = 3

    # Update score (level points for correct answer, -1 for wrong answer)
    if answer == self.answer:
      self.score_board.update_score('active', level)
    else:
      self.score_board.update_score('active', -1)

    # Update visuals (new scores, highlight of user's answer and correct answer)
    self.score1Label = self.font.render(str(self.score_board.get_score(0)), 1, (255,255,255))
    self.score2Label = self.font.render(str(self.score_board.get_score(1)), 1, (255,255,255))

    if self.answer == 0:
      self.case1 = pygame.image.load("images/case_1_r.png").convert_alpha()
    if self.answer == 1:
      self.case2 = pygame.image.load("images/case_2_r.png").convert_alpha()
    if self.answer == 2:
      self.case3 = pygame.image.load("images/case_3_r.png").convert_alpha()

    if answer != self.answer:
      if answer == 0:
        self.case1 = pygame.image.load("images/case_1_w.png").convert_alpha()
      if answer == 1:
        self.case2 = pygame.image.load("images/case_2_w.png").convert_alpha()
      if answer == 2:
        self.case3 = pygame.image.load("images/case_3_w.png").convert_alpha()

    self.on_render()


  # Handle incoming events
  def on_event(self, event):

    # Closing the window stops the game
    if event.type == pygame.QUIT:
      self.cleanup()

    # Handle keys
    if  event.type == pygame.KEYDOWN:

      # Escape stops the game
      if event.key == pygame.K_ESCAPE:
        self.cleanup()

      # 1,2,3 are used for answers
      if event.key == pygame.K_1:
        self.on_answer(0)
      if event.key == pygame.K_2:
        self.on_answer(1)
      if event.key == pygame.K_3:
        self.on_answer(2)

      # Space and Return are used as buzzers
      if event.key == pygame.K_SPACE:
        self.on_guess(0)
      if event.key == pygame.K_RETURN:
        self.on_guess(1)

      # Right arrow starts the next task
      if event.key == pygame.K_RIGHT:
        self.mode = 0
        self.startTask()


  # Update timers and corresponding screen changes
  def on_loop(self):

    # In guess mode we keep track of time as faster guesses get more points
    if self.mode == 0:
      tick = self.taskTimer.get_progress()
      stick = "{0:.1f}".format(tick)
      color = (239,35,8)
      if tick < 5:
        color = (0,164,33)
      if tick >= 5 and tick < 20:
        color = (239,216,8)
      self.timerLabel = self.fontTimer.render(stick, 1, color)
      self.on_render()

    # In answer mode we keep track of answer delay, if user did not 
    # answer within 5 seconds, the other user gets to answer
    if self.mode == 1:
      tick = 5 - self.guessTimer.get_progress()
      if tick < 0:
        tick = 0

      stick = "{0:.1f}".format(tick)
      color = (239,35,8)
      self.active = pygame.image.load("images/guess3.png").convert_alpha()
      if tick > 3:
        color = (0,164,33)
        self.active = pygame.image.load("images/guess1.png").convert_alpha()
      if tick <= 3 and tick > 2:
        color = (239,216,8)
        self.active = pygame.image.load("images/guess2.png").convert_alpha()

      self.timerLabel = self.fontTimer.render(stick, 1, color)


      if tick <= 0:
        self.guessTimer.stop()
        self.active = pygame.image.load("images/guess1.png").convert_alpha()
        self.score_board.update_score('active', -1)
        self.score_board.toggle_active()
        self.mode = 2

      self.on_render()


  # Render current screen
  def on_render(self):
    self.screen.blit(self.back, (0, 0))
    self.screen.blit(self.cover1, (47+48, 63))
    self.screen.blit(self.case1, (47, 0))
    self.screen.blit(self.cover2, (435+48, 63))
    self.screen.blit(self.case2, (435, 0))
    self.screen.blit(self.cover3, (823+48,63))
    self.screen.blit(self.case3, (823,0))

    self.screen.blit(self.name1Label, (100, 435))
    self.screen.blit(self.score1Label, (100, 485))
    self.screen.blit(self.name2Label, (1070, 435))
    self.screen.blit(self.score2Label, (1070, 485))

    textpos = self.timerLabel.get_rect()
    textwidth = tuple(textpos)[2]
    self.screen.blit(self.timerLabel, (640-(textwidth/2), 435))

    if self.mode == 1 or self.mode == 2:
      if self.score_board.active_user == 0:
        self.screen.blit(self.active, (15, 445))
      if self.score_board.active_user == 1:
        self.screen.blit(self.active, (985, 445))

    pygame.display.flip()


  # Clean stop of application
  def cleanup(self):
    self.running = False
    pygame.quit()


  # Run quiz
  def execute(self):
    while(self.running):
      self.on_loop()
      for event in pygame.event.get():
        self.on_event(event)




if __name__ == "__main__" :
  if len(sys.argv) != 4:
    print "Usage: quiz.py user1name user2name path/to/episodes"
    sys.exit(0)
  theApp = Quiz(sys.argv[1], sys.argv[2], sys.argv[3])
  theApp.execute()













