import math
import copy

BALL_RADIUS = 20
POCKET_RADIUS = BALL_RADIUS * 2 
FRICTION = 0.992  
MIN_VELOCITY = 0.01  
WIDTH = 1080
HEIGHT = 540



POCKETS = [
            (0, 0),          # Top-left
            (WIDTH // 2, 0), # Top-middle
            (WIDTH, 0),      # Top-right
            (0, HEIGHT),     # Bottom-left
            (WIDTH // 2, HEIGHT), # Bottom-middle
            (WIDTH, HEIGHT)  # Bottom-right
        ]

def merge(memory1, memory2):
    memory = None
    if memory1 is None:
        memory = memory2.merge(memory1)
    else:
        memory = memory1.merge(memory2)

    return memory

class Analyzer:
    def __init__(self, balls, initial_velocity, initial_angle, randomness):
        self.balls = []
        for ball in balls:
            if getattr(ball, 'is_cue_ball', False):
                # White ball: velocity_x and velocity_y are intervals due to randomness
                angle_rad = math.radians(initial_angle)
                v_min = initial_velocity
                v_max = initial_velocity + randomness
                vx1 = v_min * math.cos(angle_rad)
                vx2 = v_max * math.cos(angle_rad)
                vx_interval = Interval(min(vx1, vx2), max(vx1, vx2))

                vy1 = v_min * math.sin(angle_rad)
                vy2 = v_max * math.sin(angle_rad)
                vy_interval = Interval(min(vy1, vy2), max(vy1, vy2))
                self.balls.append(BallMemory(
                    Interval(ball.x, ball.x),
                    Interval(ball.y, ball.y),
                    vx_interval,
                    vy_interval,
                    Interval(1, 1),  # alive
                    True
                ))
            else:
                # Other balls: velocity_x and velocity_y are 0
                self.balls.append(BallMemory(
                    Interval(ball.x, ball.x),
                    Interval(ball.y, ball.y),
                    Interval(0, 0),
                    Interval(0, 0),
                    Interval(1, 1),  # alive
                    False
                ))
        self.history = []

    def update(self):
        """
        Dataflow analysis update: one step of interval-based simulation for all balls.
        Returns True if all balls have stopped (velocities in [0, MIN_VELOCITY]), False otherwise.
        """

        
        for i in range(len(self.balls)):
            ball = copy.deepcopy(self.balls[i])
            # split ball.alive: 
            interval_1, interval_2 = ball.alive.split_alive()
            ball_1 = copy.deepcopy(ball)
            ball_2 = copy.deepcopy(ball)
            # ball.alive if
            if (not (interval_1 is None)):
                ball_1.x = ball_1.x.add(ball_1.velocity_x)
                ball_1.y = ball_1.y.add(ball_1.velocity_y)

                ball_1.velocity_x = ball_1.velocity_x.mul_con(FRICTION)
                ball_1.velocity_y = ball_1.velocity_y.mul_con(FRICTION)

                if ball.velocity_x.abs().high < MIN_VELOCITY and ball.velocity_y.abs().high < MIN_VELOCITY:
                    ball_1.velocity_x = Interval(0, 0) 

                # Wall collision x
                ball_1_ = copy.deepcopy(ball_1)
                # ball.x - ball.radius < 0:
                interval_1_1, interval_1_2 = ball_1_.x.split('<', BALL_RADIUS)
                ball_1_1 = copy.deepcopy(ball_1_)
                ball_1_2 = copy.deepcopy(ball_1_)
                # ball.x - ball.radius < 0 if:
                if (interval_1_1):
                    ball_1_1.x = interval_1_1
                    ball_1_1.x = Interval(BALL_RADIUS, BALL_RADIUS)
                    ball_1_1.velocity_x = ball_1_1.velocity_x.mul_con(-0.9)
                else:
                    ball_1_1 = None

                # ball.x - ball.radius < 0 else:
                if (interval_1_2):
                    ball_1_2.x = interval_1_2
                    
                    ball_1_2_ = copy.deepcopy(ball_1_2)
                    # ball.x + ball.radius > WIDTH:
                    interval_1_2_1, interval_1_2_2 = ball_1_2_.x.split('>', WIDTH - BALL_RADIUS)
                    ball_1_2_1 = copy.deepcopy(ball_1_2_)
                    ball_1_2_2 = copy.deepcopy(ball_1_2_)
                    # ball.x + ball.radius > WIDTH if:
                    if (interval_1_2_1):
                        ball_1_2_1.x = interval_1_2_1
                        ball_1_2_1.x = Interval(WIDTH - BALL_RADIUS, WIDTH - BALL_RADIUS)
                        ball_1_2_1.velocity_x = ball_1_2_1.velocity_x.mul_con(-0.9)
                    else:
                        ball_1_2_1 = None
                    
                    # ball.x + ball.radius > WIDTH else:
                    if (interval_1_2_2):
                        ball_1_2_2.x = interval_1_2_2
                    else:
                        ball_1_2_2 = None
                    
                    # merge
                    ball_1_2 = merge(ball_1_2_1, ball_1_2_2)

                else:
                    ball_1_2 = None
                # merge ball.x - ball.radius < 0:
                ball_1 = merge(ball_1_1, ball_1_2)


                # Wall collision y
                ball_1_ = copy.deepcopy(ball_1)
                # ball.y - ball.radius < 0:
                interval_1_1, interval_1_2 = ball_1_.y.split('<', BALL_RADIUS)
                ball_1_1 = copy.deepcopy(ball_1_)
                ball_1_2 = copy.deepcopy(ball_1_)
                # ball.y - ball.radius < 0 if:
                if (interval_1_1):
                    ball_1_1.y = interval_1_1
                    ball_1_1.y = Interval(BALL_RADIUS, BALL_RADIUS)
                    ball_1_1.velocity_y = ball_1_1.velocity_y.mul_con(-0.9)
                else:
                    ball_1_1 = None

                # ball.y - ball.radius < 0 else:
                if (interval_1_2):
                    ball_1_2.y = interval_1_2
                    
                    ball_1_2_ = copy.deepcopy(ball_1_2)
                    # ball.y + ball.radius > HEIGHT:
                    interval_1_2_1, interval_1_2_2 = ball_1_2_.y.split('>', HEIGHT - BALL_RADIUS)
                    ball_1_2_1 = copy.deepcopy(ball_1_2_)
                    ball_1_2_2 = copy.deepcopy(ball_1_2_)
                    # ball.y + ball.radius > HEIGHT if:
                    if (interval_1_2_1):
                        ball_1_2_1.y = interval_1_2_1
                        ball_1_2_1.y = Interval(HEIGHT - BALL_RADIUS, HEIGHT - BALL_RADIUS)
                        ball_1_2_1.velocity_y = ball_1_2.velocity_y.mul_con(-0.9)
                    else:
                        ball_1_2_1 = None
                    
                    # ball.y + ball.radius > HEIGHT else:
                    if (interval_1_2_2):
                        ball_1_2_2.y = interval_1_2_2
                    else:
                        ball_1_2_2 = None
                    
                    ball_1_2 = merge(ball_1_2_1, ball_1_2_2)

                else:
                    ball_1_2 = None
                # merge ball.y - ball.radius < 0:
                ball_1 = merge(ball_1_1, ball_1_2)


            

                for pocket_x, pocket_y in POCKETS:
                    ball_1_ = copy.deepcopy(ball_1)
                    x_high = ball_1_.x.sub_con(pocket_x).abs().high
                    y_high = ball_1_.y.sub_con(pocket_y).abs().high
                    distance_high = math.sqrt(x_high * x_high + y_high * y_high)

                    x_low = ball_1_.x.sub_con(pocket_x).abs().low
                    y_low = ball_1_.y.sub_con(pocket_y).abs().low
                    distance_low = math.sqrt(x_low * x_low + y_low * y_low)
                    distance = Interval(distance_low, distance_high)

                    interval_1_1, interval_1_2 = distance.split('<', POCKET_RADIUS)
                    ball_1_1 = copy.deepcopy(ball_1_)
                    ball_1_2 = copy.deepcopy(ball_1_)

                    if (interval_1_1 and interval_1_2 is None):
                        ball_1.alive = Interval(0, 0)
                        break
                    
                    elif (interval_1_1 and interval_1_2):
                        ball_1.alive = Interval(0, 1)
                        pass
                    else:
                        pass

                ball = ball_1    

            else:
                ball = ball_2     

            self.balls[i] = ball

        # ball-ball collision
        for i, ballx in enumerate(self.balls):
            # must dead
            ball1 = copy.deepcopy(ballx)
            if (ball1.alive.high == 0):
                continue
            # may be alive
            
            for j, bally in enumerate(self.balls[i+1:], i+1):
                ball2 = copy.deepcopy(bally)
                #must dead
                if (ball2.alive.high == 0):
                    continue

                dx = ball2.x.sub(ball1.x)
                dy = ball2.y.sub(ball1.y)

                x_high = dx.abs().high
                y_high = dy.abs().high
                distance_high = math.sqrt(x_high * x_high + y_high * y_high)
                x_low = dx.abs().low
                y_low = dy.abs().low
                distance_low = math.sqrt(x_low * x_low + y_low * y_low)
                distance = Interval(distance_low, distance_high)

                if distance.low < BALL_RADIUS:
                    continue

                if distance.low < BALL_RADIUS + BALL_RADIUS:
                    # Clamp denominator to avoid division by zero or very small values

                    dist = Interval(distance.low, min(distance.high, BALL_RADIUS + BALL_RADIUS)) 

                    nx = dx.div(dist)
                    ny = dy.div(dist)
                    # Clamp nx, ny to [-1, 1] to avoid overflow
                    nx = Interval(max(-1, min(1, nx.low)), max(-1, min(1, nx.high)))
                    ny = Interval(max(-1, min(1, ny.low)), max(-1, min(1, ny.high)))

                    # Relative velocity
                    dvx = ball2.velocity_x.sub(ball1.velocity_x)
                    dvy = ball2.velocity_y.sub(ball1.velocity_y)
                    # Projected velocity along normal
                    velocity_along_normal = dvx.mul(nx).add(dvy.mul(ny))
                    if velocity_along_normal.low > 0:
                        continue  # Balls are moving apart in all cases

                    velocity_along_normal = Interval(velocity_along_normal.low, min(0, velocity_along_normal.high))
                    # Calculate impulse (as in your code, but with intervals)
                    impulse = velocity_along_normal.mul_con(1.5).div_con(2)
                    ball1.velocity_x = ball1.velocity_x.add(impulse.mul(nx))
                    ball1.velocity_y = ball1.velocity_y.add(impulse.mul(ny))
                    ball2.velocity_x = ball2.velocity_x.sub(impulse.mul(nx))
                    ball2.velocity_y = ball2.velocity_y.sub(impulse.mul(ny))

                    # Resolve overlap (conservatively)
                    overlap = dist.mul_con(-1).add_con(BALL_RADIUS + BALL_RADIUS).div_con(2)
                    ball1.x = ball1.x.sub(overlap.mul(nx))
                    ball1.y = ball1.y.sub(overlap.mul(ny))
                    ball2.x = ball2.x.add(overlap.mul(nx))
                    ball2.y = ball2.y.add(overlap.mul(ny))
                    
                    self.balls[i] = ball1
                    self.balls[j] = ball2

        all_stopped = True
        for ball in self.balls:
            if (ball.velocity_x.abs().high > MIN_VELOCITY or ball.velocity_y.abs().high > MIN_VELOCITY):
                all_stopped = False
                break

        
        return all_stopped
    

    def predict(self):
        for i in range(1000):
            result = self.update()
            self.history.append(copy.deepcopy(self.balls))
            if result:
                print(i)
                break
        return self.balls, self.history



class Interval:
    def __init__(self, low, high):
        self.low = low
        self.high = high
    def __repr__(self):
        return f"[{self.low}, {self.high}]"
    def __eq__(self, other):
        return isinstance(other, Interval) and self.low == other.low and self.high == other.high
    def merge(self, other):
        return Interval(min(self.low, other.low), max(self.high, other.high))
    def add(self, other):
        return Interval(self.low + other.low, self.high + other.high)
    def add_con(self, constant):
        return Interval(self.low + constant, self.high + constant)
    def sub(self, other):
        return Interval(self.low - other.high, self.high - other.low)
    def sub_con(self, constant):
        return Interval(self.low - constant, self.high - constant)
    def mul(self, other):
        products = [self.low * other.low, self.low * other.high, self.high * other.low, self.high * other.high]
        return Interval(min(products), max(products))
    def mul_con(self, constant):
        if constant < 0:
            return Interval(self.high * constant, self.low * constant)
        else:
            return Interval(self.low * constant, self.high * constant)
        
    def abs(self):
        if self.low >= 0:
            return Interval(self.low, self.high)
        elif self.high <= 0:
            return Interval(-self.high, -self.low)
        else:
            return Interval(0, max(abs(self.low), abs(self.high)))

    def div(self, other):
        # Avoid division by zero: if zero in denominator interval, return full range
        if other.low <= 0 <= other.high:
            return Interval(float('-inf'), float('inf'))
        quotients = [self.low / other.low, self.low / other.high, self.high / other.low, self.high / other.high]
        return Interval(min(quotients), max(quotients))
    def div_con(self, constant):
        if constant == 0:
            return Interval(float('-inf'), float('inf'))
        elif constant < 0:
            return Interval(self.high / constant, self.low / constant)
        else:
            return Interval(self.low / constant, self.high / constant)
    
    def split_alive(self):
        if self.high == 1 and self.low == 1:
            return (Interval(self.low, self.high),  None)
        elif self.high == 1 and self.low == 0:
            return (Interval(self.high, self.high),  Interval(self.low, self.low))
        else:
            return (None,  Interval(self.low, self.low))
    
    
    def split(self, op, value):
        """
        Split the interval by a comparison (>, <, >=, <=, ==) with a constant value.
        Returns a tuple (interval_if_true, interval_if_false).
        """
        if op == '>':
            if self.high <= value:
                return (None, Interval(self.low, self.high))
            elif self.low > value:
                return (Interval(self.low, self.high), None)
            else:
                return (Interval(max(self.low, value + 1e-9), self.high), Interval(self.low, min(self.high, value)))
        elif op == '>=':
            if self.high < value:
                return (None, Interval(self.low, self.high))
            elif self.low >= value:
                return (Interval(self.low, self.high), None)
            else:
                return (Interval(max(self.low, value), self.high), Interval(self.low, min(self.high, value - 1e-9)))
        elif op == '<':
            if self.low >= value:
                return (None, Interval(self.low, self.high))
            elif self.high < value:
                return (Interval(self.low, self.high), None)
            else:
                return (Interval(self.low, min(self.high, value - 1e-9)), Interval(max(self.low, value), self.high))
        elif op == '<=':
            if self.low > value:
                return (None, Interval(self.low, self.high))
            elif self.high <= value:
                return (Interval(self.low, self.high), None)
            else:
                return (Interval(self.low, min(self.high, value)), Interval(max(self.low, value + 1e-9), self.high))
        elif op == '==':
            if value < self.low or value > self.high:
                return (None, Interval(self.low, self.high))
            else:
                return (Interval(value, value), Interval(self.low, value - 1e-9) if value > self.low else None if value == self.low else None, Interval(value + 1e-9, self.high) if value < self.high else None if value == self.high else None)
        else:
            raise NotImplementedError(f"Unknown op: {op}")

class BallMemory:
    def __init__(self, x, y, velocity_x, velocity_y, alive, is_cue_ball):
        self.x = x  # Interval
        self.y = y  # Interval
        self.velocity_x = velocity_x  # Interval
        self.velocity_y = velocity_y  # Interval
        # Alive: [0, 0] means False, [1, 1] means True, [0, 1] means unknown (could be either)
        self.alive = alive  # Interval
        self.is_cue_ball = is_cue_ball  # Boolean flag for cue ball
    def __repr__(self):
        return (f"BallMemory(x={self.x}, y={self.y}, vx={self.velocity_x}, vy={self.velocity_y}, "
                f"alive={self.alive})")
    def merge(self, other):
        if (other is None):
            return BallMemory(self.x, self.y, self.velocity_x, self.velocity_y, self.alive, self.is_cue_ball)
        return BallMemory(
            self.x.merge(other.x),
            self.y.merge(other.y),
            self.velocity_x.merge(other.velocity_x),
            self.velocity_y.merge(other.velocity_y),
            self.alive.merge(other.alive),
            self.is_cue_ball
        )

