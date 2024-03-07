( define 
    (problem group_num_05) 
    (:domain group_number)

    (:agents
        a b
    )
    (:objects 
        c
    )

    (:variables
        (peeking [ a , b ])
        (num [c])
    )

    (:init
        (= (peeking a) 'f')
        (= (peeking b) 'f')
        (= (num c) 2)
        ;todo: put the initial state's facts and numeric values here
    )

    (:goal (and
        ; (= (:ontic (= (dir b) 'se'))
        (= (:epistemic cb [a,b] (< (num c) 2)) -1)
        (= (:epistemic eb [a,b] eb [a,b] (< (num c) 2)) 1)
        (= (:epistemic eb [a,b] eb [a,b] eb [a,b] eb [a,b] (= (num c) 2)) 1)
        ; (= (:epistemic eb [a,b] (< (num c) 2)) 1)
        ; (= (:epistemic b [b] (= (face c) 'tail')) 1)
        ; (= (:epistemic b [b] b [a] (= (face c) 'head')) 1)
        ; (= (:epistemic b [b] (= (face c) 'head')) 1)
        ; (= (:epistemic k [b] k [a] (= (v p) 't')) 0)
        ; (= (:epistemic s [b] s [a] (= (v p) 't')) 2)
        ; (= (:epistemic k [b] s [a] (= (v p) 't')) 2)
        ; (= (:epistemic s [a] (= (v p) 't')) 1)
        ; (= (:epistemic b [a] (= (v p) 't')) 1)
        ; (= (:epistemic b [b] (= (v p) 't')) 1)
        ;todo: put the goal condition here
    ))

    (:domains
        ; (dir enumerate ['w','nw','n','ne','e','se','s','sw'])
        ; (x integer [0,4])
        ; (y integer [0,4])
        (peeking enumerate ['t','f'])
        (num integer [0,4])
        ;(epistemic epistemic ['1','0','2']) true false unknown
    )



    ;un-comment the following line if metric is needed
    ;(:metric minimize (???))
)
